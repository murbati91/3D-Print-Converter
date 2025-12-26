#!/usr/bin/env python3
"""
CAD-to-3D Print Conversion Server
=================================
FastAPI-based REST API for file conversion.

This server can run on a Raspberry Pi, PC, or cloud server
to provide conversion capabilities to the ESP32 controller.

Author: Tech Sierra Solutions
License: MIT
"""

import os
import sys
import asyncio
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

# Import our conversion engine
from converter_engine import CADConverter, ConversionSettings, OutputFormat, ConversionResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# DATA MODELS
# =============================================================================

class ConversionRequest(BaseModel):
    output_format: str = "stl"
    extrusion_height: float = 10.0
    scale_factor: float = 1.0
    generate_gcode: bool = False
    # Slicer settings
    layer_height: float = 0.2
    infill_percentage: int = 20
    support_enabled: bool = False


class ConversionStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    input_file: str
    output_file: Optional[str] = None
    progress: int = 0
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class SystemStatus(BaseModel):
    version: str
    uptime: float
    jobs_completed: int
    jobs_pending: int
    tools_available: dict


# =============================================================================
# APPLICATION STATE
# =============================================================================

class AppState:
    def __init__(self):
        self.work_dir = tempfile.mkdtemp(prefix="3d_converter_")
        self.jobs: dict[str, ConversionStatus] = {}
        self.jobs_completed = 0
        self.start_time = datetime.now()
        
        # Create directories
        os.makedirs(os.path.join(self.work_dir, "uploads"), exist_ok=True)
        os.makedirs(os.path.join(self.work_dir, "outputs"), exist_ok=True)
        os.makedirs(os.path.join(self.work_dir, "temp"), exist_ok=True)
        
        # Initialize converter
        self.converter = CADConverter(work_dir=os.path.join(self.work_dir, "temp"))
        
        logger.info(f"Server initialized. Work directory: {self.work_dir}")


state = AppState()


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="CAD-to-3D Print Converter API",
    description="Convert CAD files (DWG, DGN, DXF, PDF) to 3D printable formats",
    version="1.0.0",
)

# CORS for ESP32 and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Welcome endpoint."""
    return {
        "name": "CAD-to-3D Print Converter API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "/status"
    }


@app.get("/status", response_model=SystemStatus)
async def get_status():
    """Get system status."""
    uptime = (datetime.now() - state.start_time).total_seconds()
    pending = sum(1 for j in state.jobs.values() if j.status in ["pending", "processing"])
    
    return SystemStatus(
        version="1.0.0",
        uptime=uptime,
        jobs_completed=state.jobs_completed,
        jobs_pending=pending,
        tools_available=state.converter.tools.check_all()
    )


@app.post("/api/convert")
async def convert_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    x_filename: Optional[str] = Header(None),
    output_format: str = "gcode",
    extrusion_height: float = 10.0,
    scale_factor: float = 1.0,
):
    """
    Convert a CAD file to 3D printable format.
    
    Supports streaming response for ESP32 clients.
    """
    
    # Generate job ID
    job_id = str(uuid.uuid4())[:8]
    
    # Determine filename
    filename = x_filename or file.filename or f"upload_{job_id}"
    
    # Save uploaded file
    input_path = os.path.join(state.work_dir, "uploads", f"{job_id}_{filename}")
    
    try:
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Job {job_id}: Saved file {filename} ({len(content)} bytes)")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    # Create job status
    status = ConversionStatus(
        job_id=job_id,
        status="processing",
        input_file=filename,
        progress=0,
        created_at=datetime.now()
    )
    state.jobs[job_id] = status
    
    # Configure conversion
    settings = ConversionSettings(
        extrusion_height=extrusion_height,
        scale_factor=scale_factor,
    )
    
    # Determine output format
    try:
        out_format = OutputFormat(output_format.lower())
    except ValueError:
        out_format = OutputFormat.GCODE
    
    # Output path
    output_filename = Path(filename).stem + f".{out_format.value}"
    output_path = os.path.join(state.work_dir, "outputs", f"{job_id}_{output_filename}")
    
    # Run conversion
    try:
        converter = CADConverter(settings)
        result = converter.convert(input_path, out_format, output_path)
        
        if result.success:
            status.status = "completed"
            status.output_file = output_path
            status.progress = 100
            status.completed_at = datetime.now()
            state.jobs_completed += 1
            
            logger.info(f"Job {job_id}: Conversion successful")
            
            # Stream the output file
            def file_iterator():
                with open(output_path, "rb") as f:
                    while chunk := f.read(8192):
                        yield chunk
            
            return StreamingResponse(
                file_iterator(),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename={output_filename}",
                    "X-Job-Id": job_id
                }
            )
        else:
            status.status = "failed"
            status.error = result.error_message
            raise HTTPException(status_code=500, detail=result.error_message)
            
    except Exception as e:
        status.status = "failed"
        status.error = str(e)
        logger.exception(f"Job {job_id}: Conversion failed")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup temp files (keep outputs for a while)
        try:
            os.remove(input_path)
        except:
            pass


@app.post("/api/convert/async")
async def convert_file_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    output_format: str = "gcode",
    extrusion_height: float = 10.0,
    scale_factor: float = 1.0,
):
    """
    Start an async conversion job.
    Returns job ID for polling status.
    """
    
    job_id = str(uuid.uuid4())[:8]
    filename = file.filename or f"upload_{job_id}"
    
    # Save uploaded file
    input_path = os.path.join(state.work_dir, "uploads", f"{job_id}_{filename}")
    
    with open(input_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create job
    status = ConversionStatus(
        job_id=job_id,
        status="pending",
        input_file=filename,
        progress=0,
        created_at=datetime.now()
    )
    state.jobs[job_id] = status
    
    # Start background conversion
    background_tasks.add_task(
        run_conversion,
        job_id,
        input_path,
        output_format,
        extrusion_height,
        scale_factor
    )
    
    return {"job_id": job_id, "status": "pending"}


async def run_conversion(
    job_id: str,
    input_path: str,
    output_format: str,
    extrusion_height: float,
    scale_factor: float
):
    """Background task for conversion."""
    
    status = state.jobs[job_id]
    status.status = "processing"
    
    settings = ConversionSettings(
        extrusion_height=extrusion_height,
        scale_factor=scale_factor,
    )
    
    try:
        out_format = OutputFormat(output_format.lower())
    except ValueError:
        out_format = OutputFormat.GCODE
    
    output_filename = Path(status.input_file).stem + f".{out_format.value}"
    output_path = os.path.join(state.work_dir, "outputs", f"{job_id}_{output_filename}")
    
    try:
        converter = CADConverter(settings)
        result = converter.convert(input_path, out_format, output_path)
        
        if result.success:
            status.status = "completed"
            status.output_file = output_path
            status.progress = 100
            status.completed_at = datetime.now()
            state.jobs_completed += 1
        else:
            status.status = "failed"
            status.error = result.error_message
            
    except Exception as e:
        status.status = "failed"
        status.error = str(e)
    
    finally:
        try:
            os.remove(input_path)
        except:
            pass


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a conversion job."""
    
    if job_id not in state.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return state.jobs[job_id]


@app.get("/api/jobs/{job_id}/download")
async def download_result(job_id: str):
    """Download the converted file."""
    
    if job_id not in state.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = state.jobs[job_id]
    
    if status.status != "completed":
        raise HTTPException(status_code=400, detail=f"Job status: {status.status}")
    
    if not status.output_file or not os.path.exists(status.output_file):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        status.output_file,
        filename=os.path.basename(status.output_file),
        media_type="application/octet-stream"
    )


@app.get("/api/jobs")
async def list_jobs(limit: int = 50):
    """List recent conversion jobs."""
    
    jobs = sorted(
        state.jobs.values(),
        key=lambda j: j.created_at,
        reverse=True
    )[:limit]
    
    return {"jobs": jobs}


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its files."""
    
    if job_id not in state.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = state.jobs[job_id]
    
    # Delete output file
    if status.output_file and os.path.exists(status.output_file):
        os.remove(status.output_file)
    
    del state.jobs[job_id]
    
    return {"deleted": job_id}


@app.get("/api/formats")
async def list_formats():
    """List supported input and output formats."""
    
    return {
        "input_formats": ["dwg", "dgn", "dxf", "pdf", "dat", "svg"],
        "output_formats": ["stl", "obj", "gcode", "3mf", "step"],
        "tools": state.converter.tools.check_all()
    }


# =============================================================================
# STARTUP AND SHUTDOWN
# =============================================================================

@app.on_event("startup")
async def startup():
    logger.info("Starting CAD-to-3D Print Converter Server")
    
    # Check tools
    tools = state.converter.tools.check_all()
    logger.info(f"Available tools: {tools}")
    
    missing = [name for name, available in tools.items() if not available]
    if missing:
        logger.warning(f"Missing tools: {missing}")
        logger.warning("Some conversion features may not be available")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down server")
    
    # Cleanup work directory
    try:
        shutil.rmtree(state.work_dir)
    except:
        pass


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="CAD-to-3D Print Conversion Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
