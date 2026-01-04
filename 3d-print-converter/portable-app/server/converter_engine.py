#!/usr/bin/env python3
"""
CAD-to-3D Print Converter Engine
================================
Open-source file conversion pipeline for 3D printing.

Supports: DWG, DGN, DXF, PDF, DAT → STL/G-code

Author: Tech Sierra Solutions
License: MIT
"""

import os
import sys
import subprocess
import tempfile
import shutil
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib

# Third-party imports
import numpy as np
from rich.console import Console
import ezdxf
import trimesh

# Configure console with safe encoding for Windows
console = Console(legacy_windows=False, force_terminal=False)
logger = logging.getLogger(__name__)


class FileType(Enum):
    """Supported input file types."""
    DWG = "dwg"
    DGN = "dgn"
    DXF = "dxf"
    PDF = "pdf"
    DAT = "dat"
    SVG = "svg"
    UNKNOWN = "unknown"


class OutputFormat(Enum):
    """Supported output formats."""
    STL = "stl"
    OBJ = "obj"
    STEP = "step"
    GCODE = "gcode"
    THREE_MF = "3mf"


@dataclass
class ConversionSettings:
    """Settings for the conversion process."""
    extrusion_height: float = 10.0  # mm
    scale_factor: float = 1.0
    center_model: bool = True
    repair_mesh: bool = True
    simplify_mesh: bool = False
    simplify_ratio: float = 0.5
    
    # Slicer settings (for G-code)
    layer_height: float = 0.2  # mm
    nozzle_diameter: float = 0.4  # mm
    print_speed: float = 50.0  # mm/s
    infill_percentage: int = 20
    support_enabled: bool = False
    
    # Bed settings
    bed_size_x: float = 220.0  # mm
    bed_size_y: float = 220.0  # mm
    bed_size_z: float = 250.0  # mm


@dataclass
class ConversionResult:
    """Result of a conversion operation."""
    success: bool
    input_file: str
    output_file: Optional[str] = None
    output_format: Optional[OutputFormat] = None
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "input_file": self.input_file,
            "output_file": self.output_file,
            "output_format": self.output_format.value if self.output_format else None,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "metadata": self.metadata
        }


class ExternalToolPaths:
    """Paths to external conversion tools."""
    
    def __init__(self):
        self.oda_converter = self._find_oda_converter()
        self.inkscape = self._find_inkscape()
        self.freecad = self._find_freecad()
        self.openscad = self._find_openscad()
        self.prusaslicer = self._find_prusaslicer()
    
    def _find_executable(self, names: List[str], paths: List[str] = None) -> Optional[str]:
        """Find an executable by name in system PATH or specified paths."""
        search_paths = paths or []
        
        # Add common installation paths
        if sys.platform == "win32":
            import os as _os
            user_home = _os.path.expanduser("~")
            search_paths.extend([
                r"C:\Program Files\ODA",
                r"C:\Program Files\ODA\ODAFileConverter",
                r"C:\Program Files\ODA\ODAFileConverter 26.10.0",
                r"C:\Program Files\FreeCAD",
                r"C:\Program Files\FreeCAD\bin",
                f"{user_home}\\AppData\\Local\\Programs\\FreeCAD 1.0\\bin",
                r"C:\Program Files\Inkscape",
                r"C:\Program Files\Inkscape\bin",
                r"C:\Program Files\OpenSCAD",
                r"C:\Program Files\Prusa3D\PrusaSlicer",
            ])
        else:
            search_paths.extend([
                "/usr/bin",
                "/usr/local/bin",
                "/opt/freecad/bin",
                "/Applications/FreeCAD.app/Contents/MacOS",
            ])
        
        for name in names:
            # Check system PATH
            result = shutil.which(name)
            if result:
                return result
            
            # Check specific paths
            for path in search_paths:
                full_path = os.path.join(path, name)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    return full_path
                # Windows: add .exe
                if sys.platform == "win32":
                    full_path_exe = full_path + ".exe"
                    if os.path.isfile(full_path_exe):
                        return full_path_exe
        
        return None
    
    def _find_oda_converter(self) -> Optional[str]:
        return self._find_executable([
            "ODAFileConverter",
            "TeighaFileConverter", 
            "odafileconverter"
        ])
    
    def _find_inkscape(self) -> Optional[str]:
        return self._find_executable(["inkscape"])
    
    def _find_freecad(self) -> Optional[str]:
        return self._find_executable([
            "freecad",
            "FreeCAD", 
            "freecadcmd",
            "FreeCADCmd"
        ])
    
    def _find_openscad(self) -> Optional[str]:
        return self._find_executable(["openscad", "OpenSCAD"])
    
    def _find_prusaslicer(self) -> Optional[str]:
        return self._find_executable([
            "prusa-slicer",
            "prusaslicer",
            "PrusaSlicer",
            "slic3r"
        ])
    
    def check_all(self) -> Dict[str, bool]:
        """Check availability of all external tools."""
        return {
            "oda_converter": self.oda_converter is not None,
            "inkscape": self.inkscape is not None,
            "freecad": self.freecad is not None,
            "openscad": self.openscad is not None,
            "prusaslicer": self.prusaslicer is not None,
        }


class CADConverter:
    """
    Main conversion engine for CAD files to 3D printable formats.
    """
    
    def __init__(self, settings: ConversionSettings = None, work_dir: str = None):
        self.settings = settings or ConversionSettings()
        self.work_dir = work_dir or tempfile.mkdtemp(prefix="cad_converter_")
        self.tools = ExternalToolPaths()
        
        # Create work directory structure
        os.makedirs(os.path.join(self.work_dir, "input"), exist_ok=True)
        os.makedirs(os.path.join(self.work_dir, "intermediate"), exist_ok=True)
        os.makedirs(os.path.join(self.work_dir, "output"), exist_ok=True)
        
        logger.info(f"CADConverter initialized. Work directory: {self.work_dir}")
    
    def detect_file_type(self, file_path: str) -> FileType:
        """Detect the type of input file."""
        ext = Path(file_path).suffix.lower().lstrip(".")
        
        type_map = {
            "dwg": FileType.DWG,
            "dgn": FileType.DGN,
            "dxf": FileType.DXF,
            "pdf": FileType.PDF,
            "dat": FileType.DAT,
            "svg": FileType.SVG,
        }
        
        return type_map.get(ext, FileType.UNKNOWN)
    
    def convert(
        self,
        input_file: str,
        output_format: OutputFormat = OutputFormat.STL,
        output_path: str = None
    ) -> ConversionResult:
        """
        Main conversion entry point.
        
        Args:
            input_file: Path to input file
            output_format: Desired output format
            output_path: Optional output path (auto-generated if not provided)
        
        Returns:
            ConversionResult with status and output file path
        """
        logger.info(f"Starting conversion: {input_file}")
        
        # Validate input
        if not os.path.exists(input_file):
            return ConversionResult(
                success=False,
                input_file=input_file,
                error_message=f"Input file not found: {input_file}"
            )
        
        file_type = self.detect_file_type(input_file)
        if file_type == FileType.UNKNOWN:
            return ConversionResult(
                success=False,
                input_file=input_file,
                error_message=f"Unknown file type: {Path(input_file).suffix}"
            )
        
        # Generate output path if not provided
        if not output_path:
            output_name = Path(input_file).stem + f".{output_format.value}"
            output_path = os.path.join(self.work_dir, "output", output_name)
        
        try:
            # Step 1: Convert to intermediate format (DXF)
            logger.info("Converting to intermediate format...")
            dxf_file = self._convert_to_dxf(input_file, file_type)

            # Step 2: Process DXF and create 3D geometry
            logger.info("Creating 3D geometry...")
            mesh = self._dxf_to_mesh(dxf_file)

            # Step 3: Process mesh (repair, scale, center)
            logger.info("Processing mesh...")
            mesh = self._process_mesh(mesh)

            # Step 4: Export to desired format
            logger.info(f"Exporting to {output_format.value}...")
            self._export_mesh(mesh, output_path, output_format)

            # Step 5: Generate G-code if requested
            if output_format == OutputFormat.GCODE:
                logger.info("Generating G-code...")
                stl_path = output_path.replace(".gcode", ".stl")
                self._export_mesh(mesh, stl_path, OutputFormat.STL)
                self._generate_gcode(stl_path, output_path)
            
            logger.info(f"Conversion successful: {output_path}")
            
            return ConversionResult(
                success=True,
                input_file=input_file,
                output_file=output_path,
                output_format=output_format,
                metadata={
                    "vertices": len(mesh.vertices) if hasattr(mesh, 'vertices') else 0,
                    "faces": len(mesh.faces) if hasattr(mesh, 'faces') else 0,
                    "bounds": mesh.bounds.tolist() if hasattr(mesh, 'bounds') else None,
                }
            )
            
        except Exception as e:
            logger.exception(f"Conversion failed: {e}")
            return ConversionResult(
                success=False,
                input_file=input_file,
                error_message=str(e)
            )
    
    def _convert_to_dxf(self, input_file: str, file_type: FileType) -> str:
        """Convert input file to DXF intermediate format."""
        
        if file_type == FileType.DXF:
            return input_file
        
        output_dxf = os.path.join(
            self.work_dir, "intermediate",
            Path(input_file).stem + ".dxf"
        )
        
        if file_type in [FileType.DWG, FileType.DGN]:
            self._convert_with_oda(input_file, output_dxf, file_type)
        elif file_type == FileType.PDF:
            self._convert_pdf_to_dxf(input_file, output_dxf)
        elif file_type == FileType.SVG:
            self._convert_svg_to_dxf(input_file, output_dxf)
        elif file_type == FileType.DAT:
            self._convert_dat_to_dxf(input_file, output_dxf)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return output_dxf
    
    def _convert_with_oda(self, input_file: str, output_file: str, file_type: FileType):
        """Convert DWG/DGN using ODA File Converter."""
        
        if not self.tools.oda_converter:
            raise RuntimeError(
                "ODA File Converter not found. Please install from: "
                "https://www.opendesign.com/guestfiles/oda_file_converter"
            )
        
        input_dir = os.path.dirname(input_file)
        output_dir = os.path.dirname(output_file)
        input_name = os.path.basename(input_file)
        
        # ODA converter command
        cmd = [
            self.tools.oda_converter,
            input_dir,      # Input folder
            output_dir,     # Output folder
            "ACAD2018",     # Output version
            "DXF",          # Output format
            "0",            # Recurse folders (0=no)
            "1",            # Audit (1=yes)
            input_name      # Input file filter
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"ODA conversion failed: {result.stderr}")
        
        # ODA names output file same as input but with .dxf extension
        expected_output = os.path.join(
            output_dir,
            Path(input_file).stem + ".dxf"
        )
        
        if os.path.exists(expected_output) and expected_output != output_file:
            shutil.move(expected_output, output_file)
    
    def _convert_pdf_to_dxf(self, input_file: str, output_file: str):
        """Convert PDF to DXF via SVG intermediate."""
        
        if not self.tools.inkscape:
            raise RuntimeError(
                "Inkscape not found. Please install from: https://inkscape.org/"
            )
        
        # First convert PDF to SVG
        svg_file = output_file.replace(".dxf", ".svg")
        
        cmd = [
            self.tools.inkscape,
            input_file,
            "--export-type=svg",
            f"--export-filename={svg_file}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"PDF to SVG conversion failed: {result.stderr}")
        
        # Then convert SVG to DXF
        self._convert_svg_to_dxf(svg_file, output_file)
    
    def _convert_svg_to_dxf(self, input_file: str, output_file: str):
        """Convert SVG to DXF using ezdxf."""
        
        try:
            from svgpathtools import svg2paths2
            
            # Parse SVG
            paths, attributes, svg_attributes = svg2paths2(input_file)
            
            # Create new DXF document
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            
            # Convert each path to DXF entities
            for path in paths:
                for segment in path:
                    # Convert each segment type
                    if hasattr(segment, 'start') and hasattr(segment, 'end'):
                        start = segment.start
                        end = segment.end
                        
                        # Check segment type and convert accordingly
                        segment_type = type(segment).__name__
                        
                        if segment_type == 'Line':
                            msp.add_line(
                                (start.real, start.imag),
                                (end.real, end.imag)
                            )
                        elif segment_type == 'Arc':
                            # Approximate arc with polyline
                            points = self._arc_to_points(segment, 32)
                            if len(points) > 1:
                                msp.add_lwpolyline(points)
                        elif segment_type in ['CubicBezier', 'QuadraticBezier']:
                            # Approximate bezier with polyline
                            points = self._bezier_to_points(segment, 32)
                            if len(points) > 1:
                                msp.add_lwpolyline(points)
            
            doc.saveas(output_file)
            
        except Exception as e:
            logger.warning(f"SVG conversion with ezdxf failed: {e}")
            # Fallback to Inkscape
            if self.tools.inkscape:
                cmd = [
                    self.tools.inkscape,
                    input_file,
                    "--export-type=dxf",
                    f"--export-filename={output_file}"
                ]
                subprocess.run(cmd, capture_output=True, check=True)
            else:
                raise
    
    def _convert_dat_to_dxf(self, input_file: str, output_file: str):
        """
        Convert DAT file to DXF.
        DAT files can have various formats - this handles common point cloud
        and coordinate formats.
        """
        
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        points = []
        
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Try to parse coordinates
                parts = line.replace(',', ' ').split()
                try:
                    if len(parts) >= 2:
                        x = float(parts[0])
                        y = float(parts[1])
                        z = float(parts[2]) if len(parts) >= 3 else 0.0
                        points.append((x, y, z))
                except ValueError:
                    continue
        
        if not points:
            raise ValueError("No valid coordinates found in DAT file")
        
        # Create entities based on point count
        if len(points) == 1:
            msp.add_point(points[0])
        elif len(points) == 2:
            msp.add_line(points[0], points[1])
        else:
            # Create polyline
            msp.add_lwpolyline(points)
            # Also try to create closed polygon if first == last
            if np.allclose(points[0][:2], points[-1][:2]):
                msp.add_lwpolyline(points, close=True)
        
        doc.saveas(output_file)
    
    def _dxf_to_mesh(self, dxf_file: str) -> trimesh.Trimesh:
        """Convert DXF to 3D mesh by extruding 2D profiles."""
        
        doc = ezdxf.readfile(dxf_file)
        msp = doc.modelspace()
        
        # Collect all 2D paths
        paths = []
        
        for entity in msp:
            dxftype = entity.dxftype()
            
            if dxftype == 'LINE':
                paths.append([
                    (entity.dxf.start.x, entity.dxf.start.y),
                    (entity.dxf.end.x, entity.dxf.end.y)
                ])
            
            elif dxftype == 'LWPOLYLINE':
                points = [(p[0], p[1]) for p in entity.get_points()]
                if entity.closed:
                    points.append(points[0])
                paths.append(points)
            
            elif dxftype == 'POLYLINE':
                points = [(v.dxf.location.x, v.dxf.location.y) 
                         for v in entity.vertices]
                if entity.is_closed:
                    points.append(points[0])
                paths.append(points)
            
            elif dxftype == 'CIRCLE':
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                # Approximate circle with polygon
                angles = np.linspace(0, 2*np.pi, 64)
                points = [
                    (center[0] + radius * np.cos(a),
                     center[1] + radius * np.sin(a))
                    for a in angles
                ]
                points.append(points[0])
                paths.append(points)
            
            elif dxftype == 'ARC':
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                start_angle = np.radians(entity.dxf.start_angle)
                end_angle = np.radians(entity.dxf.end_angle)
                
                if end_angle < start_angle:
                    end_angle += 2 * np.pi
                
                angles = np.linspace(start_angle, end_angle, 32)
                points = [
                    (center[0] + radius * np.cos(a),
                     center[1] + radius * np.sin(a))
                    for a in angles
                ]
                paths.append(points)
            
            elif dxftype == 'SPLINE':
                # Approximate spline
                try:
                    points = [(p.x, p.y) for p in entity.flattening(0.1)]
                    paths.append(points)
                except:
                    pass
        
        if not paths:
            raise ValueError("No valid geometry found in DXF file")
        
        # Create 2D polygon from paths
        polygon = self._paths_to_polygon(paths)
        
        # Extrude to 3D
        mesh = trimesh.creation.extrude_polygon(
            polygon,
            height=self.settings.extrusion_height
        )
        
        return mesh
    
    def _paths_to_polygon(self, paths: List[List[Tuple[float, float]]]):
        """Convert list of paths to a Shapely polygon."""
        from shapely.geometry import Polygon, MultiPolygon, LineString
        from shapely.ops import polygonize, unary_union
        
        # Create LineStrings from paths
        lines = []
        for path in paths:
            if len(path) >= 2:
                lines.append(LineString(path))
        
        if not lines:
            raise ValueError("No valid paths for polygon creation")
        
        # Try to create polygons from lines
        merged = unary_union(lines)
        polygons = list(polygonize(merged))
        
        if polygons:
            # Return the largest polygon
            return max(polygons, key=lambda p: p.area)
        
        # Fallback: create bounding box
        all_points = []
        for path in paths:
            all_points.extend(path)
        
        if all_points:
            xs, ys = zip(*all_points)
            return Polygon([
                (min(xs), min(ys)),
                (max(xs), min(ys)),
                (max(xs), max(ys)),
                (min(xs), max(ys))
            ])
        
        raise ValueError("Could not create polygon from paths")
    
    def _process_mesh(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Process mesh: repair, scale, center."""
        
        # Apply scale
        if self.settings.scale_factor != 1.0:
            mesh.apply_scale(self.settings.scale_factor)
        
        # Center on origin
        if self.settings.center_model:
            mesh.vertices -= mesh.centroid
        
        # Repair mesh
        if self.settings.repair_mesh:
            trimesh.repair.fix_normals(mesh)
            trimesh.repair.fix_inversion(mesh)
            trimesh.repair.fix_winding(mesh)
        
        # Simplify if requested
        if self.settings.simplify_mesh:
            target_faces = int(len(mesh.faces) * self.settings.simplify_ratio)
            mesh = mesh.simplify_quadric_decimation(target_faces)
        
        return mesh
    
    def _export_mesh(self, mesh: trimesh.Trimesh, output_path: str, 
                     output_format: OutputFormat):
        """Export mesh to specified format."""
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if output_format == OutputFormat.STL:
            mesh.export(output_path, file_type='stl')
        elif output_format == OutputFormat.OBJ:
            mesh.export(output_path, file_type='obj')
        elif output_format == OutputFormat.THREE_MF:
            mesh.export(output_path, file_type='3mf')
        elif output_format == OutputFormat.STEP:
            # STEP export requires FreeCAD
            self._export_step_freecad(mesh, output_path)
        elif output_format == OutputFormat.GCODE:
            # G-code is handled separately
            pass
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _export_step_freecad(self, mesh: trimesh.Trimesh, output_path: str):
        """Export to STEP format using FreeCAD."""
        
        if not self.tools.freecad:
            raise RuntimeError("FreeCAD not found for STEP export")
        
        # Save as STL first
        stl_temp = output_path.replace(".step", "_temp.stl")
        mesh.export(stl_temp, file_type='stl')
        
        # Create FreeCAD script
        script = f"""
import FreeCAD
import Mesh
import Part

mesh = Mesh.Mesh("{stl_temp}")
shape = Part.Shape()
shape.makeShapeFromMesh(mesh.Topology, 0.1)
solid = Part.makeSolid(shape)
solid.exportStep("{output_path}")
"""
        
        script_file = output_path.replace(".step", "_convert.py")
        with open(script_file, 'w') as f:
            f.write(script)
        
        # Run FreeCAD
        cmd = [self.tools.freecad, "-c", script_file]
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Cleanup
        os.remove(stl_temp)
        os.remove(script_file)
    
    def _generate_gcode(self, stl_path: str, gcode_path: str):
        """Generate G-code from STL using PrusaSlicer."""

        if not self.tools.prusaslicer:
            # Fallback to simple G-code generation
            logger.info("PrusaSlicer not found, using simple G-code generator")
            self._simple_gcode_generator(stl_path, gcode_path)
            return

        # Ensure output directory exists
        os.makedirs(os.path.dirname(gcode_path), exist_ok=True)

        # Build PrusaSlicer command with all slicer settings
        # Use separate --output argument to handle paths with spaces
        cmd = [
            self.tools.prusaslicer,
            "--export-gcode",
            "--output", gcode_path,  # Separate argument for proper path handling
            f"--layer-height={self.settings.layer_height}",
            f"--nozzle-diameter={self.settings.nozzle_diameter}",
            f"--fill-density={self.settings.infill_percentage}%",
            # Print speed settings
            f"--perimeter-speed={self.settings.print_speed}",
            f"--infill-speed={self.settings.print_speed}",
            # Bed dimensions (rectangular bed shape defined by 4 corners)
            f"--bed-shape=0x0,{self.settings.bed_size_x}x0,{self.settings.bed_size_x}x{self.settings.bed_size_y},0x{self.settings.bed_size_y}",
            stl_path
        ]

        if self.settings.support_enabled:
            cmd.append("--support-material")

        logger.info(f"Running PrusaSlicer: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Check if PrusaSlicer succeeded AND the file was created
        if result.returncode != 0:
            logger.warning(f"PrusaSlicer failed (code {result.returncode}): {result.stderr}")
            self._simple_gcode_generator(stl_path, gcode_path)
        elif not os.path.exists(gcode_path):
            logger.warning(f"PrusaSlicer returned 0 but G-code file not found at {gcode_path}")
            logger.warning(f"PrusaSlicer stdout: {result.stdout}")
            logger.warning(f"PrusaSlicer stderr: {result.stderr}")
            self._simple_gcode_generator(stl_path, gcode_path)
        else:
            logger.info(f"PrusaSlicer successfully created G-code: {gcode_path}")
    
    def _simple_gcode_generator(self, stl_path: str, gcode_path: str):
        """Simple G-code generator for basic shapes."""

        logger.info(f"Using simple G-code generator for {stl_path}")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(gcode_path), exist_ok=True)

        mesh = trimesh.load(stl_path)
        bounds = mesh.bounds
        
        # Calculate layers
        height = bounds[1][2] - bounds[0][2]
        num_layers = int(height / self.settings.layer_height)
        
        gcode_lines = [
            "; Generated by CAD-to-3D Converter",
            "; Simple G-code - for complex parts use PrusaSlicer",
            "",
            "G28 ; Home all axes",
            "G90 ; Absolute positioning",
            "M82 ; Extruder absolute mode",
            "M104 S200 ; Set extruder temp",
            "M140 S60 ; Set bed temp",
            "M109 S200 ; Wait for extruder",
            "M190 S60 ; Wait for bed",
            "G92 E0 ; Reset extruder",
            "",
        ]
        
        e_pos = 0
        layer_height = self.settings.layer_height
        
        for layer in range(num_layers):
            z = bounds[0][2] + (layer + 1) * layer_height
            gcode_lines.append(f"; Layer {layer + 1}/{num_layers}")
            gcode_lines.append(f"G1 Z{z:.3f} F3000")
            
            # Get cross-section at this height
            section = mesh.section(
                plane_origin=[0, 0, z - layer_height/2],
                plane_normal=[0, 0, 1]
            )
            
            if section is not None:
                try:
                    path, _ = section.to_planar()
                    for entity in path.entities:
                        points = path.vertices[entity.points]
                        
                        # Move to start
                        gcode_lines.append(
                            f"G0 X{points[0][0]:.3f} Y{points[0][1]:.3f} F6000"
                        )
                        
                        # Extrude along path
                        for i in range(1, len(points)):
                            dx = points[i][0] - points[i-1][0]
                            dy = points[i][1] - points[i-1][1]
                            dist = np.sqrt(dx**2 + dy**2)
                            e_pos += dist * 0.05  # Simple extrusion calc
                            
                            gcode_lines.append(
                                f"G1 X{points[i][0]:.3f} Y{points[i][1]:.3f} "
                                f"E{e_pos:.4f} F{self.settings.print_speed * 60:.0f}"
                            )
                except Exception as e:
                    logger.warning(f"Layer {layer} section failed: {e}")
        
        # End G-code
        gcode_lines.extend([
            "",
            "M104 S0 ; Turn off extruder",
            "M140 S0 ; Turn off bed",
            "G28 X Y ; Home X and Y",
            "M84 ; Disable motors",
        ])
        
        with open(gcode_path, 'w') as f:
            f.write('\n'.join(gcode_lines))

        logger.info(f"Simple G-code generator created: {gcode_path} ({num_layers} layers)")

    def _arc_to_points(self, arc, num_points: int) -> List[Tuple[float, float]]:
        """Convert arc segment to points."""
        points = []
        for i in range(num_points + 1):
            t = i / num_points
            p = arc.point(t)
            points.append((p.real, p.imag))
        return points
    
    def _bezier_to_points(self, bezier, num_points: int) -> List[Tuple[float, float]]:
        """Convert bezier segment to points."""
        points = []
        for i in range(num_points + 1):
            t = i / num_points
            p = bezier.point(t)
            points.append((p.real, p.imag))
        return points
    
    def cleanup(self):
        """Clean up temporary files."""
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)


# Command-line interface
def main():
    import click
    
    @click.command()
    @click.argument('input_file', type=click.Path(exists=True))
    @click.option('--output', '-o', type=click.Path(), help='Output file path')
    @click.option('--format', '-f', 'output_format', 
                  type=click.Choice(['stl', 'obj', 'gcode', '3mf', 'step']),
                  default='stl', help='Output format')
    @click.option('--height', '-h', type=float, default=10.0,
                  help='Extrusion height in mm')
    @click.option('--scale', '-s', type=float, default=1.0,
                  help='Scale factor')
    def convert(input_file, output, output_format, height, scale):
        """Convert CAD files to 3D printable formats."""
        
        settings = ConversionSettings(
            extrusion_height=height,
            scale_factor=scale
        )
        
        converter = CADConverter(settings)
        
        try:
            result = converter.convert(
                input_file,
                OutputFormat(output_format),
                output
            )
            
            if result.success:
                console.print(f"\n[green]Output: {result.output_file}[/green]")
            else:
                console.print(f"\n[red]Error: {result.error_message}[/red]")
                sys.exit(1)
        finally:
            converter.cleanup()
    
    convert()


if __name__ == "__main__":
    main()
