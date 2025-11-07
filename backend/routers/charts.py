"""
Charts API Router
Provides endpoints for generating various chart types
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

from backend.database import get_db
from backend.models.models import Dataset, Analysis
from backend.utils.charts import generate_chart
import os

router = APIRouter(prefix="/datasets/{dataset_id}/charts", tags=["charts"])


# Request schemas
class ChartRequest(BaseModel):
    """Base chart generation request"""
    chart_type: str = Field(..., description="Chart type: bar|timeseries|pie|distribution|heatmap")
    title: Optional[str] = Field(None, description="Chart title")


class BarChartRequest(ChartRequest):
    """Bar chart specific parameters"""
    chart_type: str = "bar"
    category_col: str = Field(..., description="Category column name")
    value_col: str = Field(default="count", description="Value column name or 'count'")
    agg: str = Field(default="sum", description="Aggregation method: sum|count|mean|median")
    top_k: int = Field(default=8, description="Show top K categories")


class TimeseriesChartRequest(ChartRequest):
    """Timeseries chart specific parameters"""
    chart_type: str = "timeseries"
    time_col: str = Field(..., description="Time column name")
    value_col: str = Field(default="count", description="Value column name or 'count'")
    freq: str = Field(default="D", description="Frequency: D|W|M")
    agg: str = Field(default="sum", description="Aggregation method: sum|count|mean|median")
    group_by: Optional[str] = Field(None, description="Group by column for multiple series")
    time_range: Optional[List[str]] = Field(None, description="Time range [start, end]")


class PieChartRequest(ChartRequest):
    """Pie chart specific parameters"""
    chart_type: str = "pie"
    category_col: str = Field(..., description="Category column name")
    value_col: str = Field(default="count", description="Value column name or 'count'")
    agg: str = Field(default="sum", description="Aggregation method: sum|count|mean|median")
    top_k: int = Field(default=8, description="Show top K categories")


class DistributionChartRequest(ChartRequest):
    """Distribution chart specific parameters"""
    chart_type: str = "distribution"
    value_col: str = Field(..., description="Value column name")
    bins: Optional[int] = Field(None, description="Number of bins (auto if None)")


class HeatmapChartRequest(ChartRequest):
    """Heatmap chart specific parameters"""
    chart_type: str = "heatmap"
    columns: Optional[List[str]] = Field(None, description="Numeric columns (auto-select if None)")


# Response schema
class ChartResponse(BaseModel):
    """Chart generation response"""
    chart_id: str
    chart_type: str
    data: List[Dict[str, Any]]
    layout: Dict[str, Any]
    meta: Dict[str, Any]
    summary: Dict[str, Any]

    class Config:
        from_attributes = True


@router.post("", response_model=ChartResponse, summary="Generate chart")
async def create_chart(
    dataset_id: int,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Generate a chart for a dataset

    Supports multiple chart types:
    - bar: Category distribution
    - timeseries: Time-based trends
    - pie: Proportion visualization
    - distribution: Value distribution histogram
    - heatmap: Correlation matrix

    Args:
        dataset_id: Dataset ID
        request: Chart configuration (type and parameters)
        db: Database session

    Returns:
        Chart configuration with Plotly JSON spec

    Raises:
        HTTPException: If dataset not found or chart generation fails
    """
    # Get dataset
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Check if file exists
    if not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")

    # Extract chart type
    chart_type = request.get("chart_type")
    if not chart_type:
        raise HTTPException(status_code=400, detail="chart_type is required")

    # Remove chart_type from kwargs to pass to generator
    chart_params = {k: v for k, v in request.items() if k != "chart_type"}

    try:
        # Generate chart
        start_time = datetime.now()
        chart_result = generate_chart(
            file_path=dataset.file_path,
            chart_type=chart_type,
            **chart_params
        )
        execution_time = (datetime.now() - start_time).total_seconds()

        # Save to analyses table
        analysis = Analysis(
            dataset_id=dataset_id,
            analysis_type=f"chart_{chart_type}",
            title=chart_params.get("title", f"{chart_type.capitalize()} Chart"),
            input_params=request,
            result_json=chart_result,
            execution_time=execution_time,
            status="completed"
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        return chart_result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {str(e)}")


@router.get("", summary="List dataset charts")
async def list_charts(
    dataset_id: int,
    chart_type: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    List all charts generated for a dataset

    Args:
        dataset_id: Dataset ID
        chart_type: Filter by chart type (optional)
        limit: Maximum number of results
        db: Database session

    Returns:
        List of chart analyses
    """
    # Check dataset exists
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Build query
    query = db.query(Analysis).filter(
        Analysis.dataset_id == dataset_id,
        Analysis.analysis_type.like("chart_%")
    )

    if chart_type:
        query = query.filter(Analysis.analysis_type == f"chart_{chart_type}")

    analyses = query.order_by(Analysis.created_at.desc()).limit(limit).all()

    return {
        "dataset_id": dataset_id,
        "total": len(analyses),
        "charts": [
            {
                "id": a.id,
                "chart_type": a.analysis_type.replace("chart_", ""),
                "title": a.title,
                "created_at": a.created_at,
                "execution_time": a.execution_time,
                "summary": a.result_json.get("summary") if a.result_json else None
            }
            for a in analyses
        ]
    }


@router.get("/{analysis_id}", response_model=ChartResponse, summary="Get chart by ID")
async def get_chart(
    dataset_id: int,
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific chart by analysis ID

    Args:
        dataset_id: Dataset ID
        analysis_id: Analysis ID
        db: Database session

    Returns:
        Chart configuration
    """
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.dataset_id == dataset_id,
        Analysis.analysis_type.like("chart_%")
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Chart not found")

    if not analysis.result_json:
        raise HTTPException(status_code=500, detail="Chart data not available")

    return analysis.result_json


@router.delete("/{analysis_id}", summary="Delete chart")
async def delete_chart(
    dataset_id: int,
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a chart analysis

    Args:
        dataset_id: Dataset ID
        analysis_id: Analysis ID
        db: Database session

    Returns:
        Success message
    """
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.dataset_id == dataset_id,
        Analysis.analysis_type.like("chart_%")
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Chart not found")

    db.delete(analysis)
    db.commit()

    return {"message": "Chart deleted successfully", "id": analysis_id}
