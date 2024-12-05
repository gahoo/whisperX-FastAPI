"""This module contains the task management routes for the FastAPI application."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from sqlalchemy.orm import Session

from ..db import get_db_session
from ..logger import logger  # Import the logger from the new module
from ..schemas import Response, Result, ResultTasks
from ..tasks import (
    delete_task_from_db,
    get_all_tasks_status_from_db,
    get_task_status_from_db,
    get_task_result_from_db,
)

task_router = APIRouter()


@task_router.get("/task/all", tags=["Tasks Management"])
async def get_all_tasks_status(
    session: Session = Depends(get_db_session),
) -> ResultTasks:
    """
    Retrieve the status of all tasks.

    Args:
        session (Session): Database session dependency.

    Returns:
        ResultTasks: The status of all tasks.
    """
    logger.info("Retrieving status of all tasks")
    return get_all_tasks_status_from_db(session)


@task_router.get("/task/{identifier}", tags=["Tasks Management"])
async def get_transcription_status(
    identifier: str,
    session: Session = Depends(get_db_session),
) -> Result:
    """
    Retrieve the status of a specific task by its identifier.

    Args:
        identifier (str): The identifier of the task.
        session (Session): Database session dependency.

    Returns:
        Result: The status of the task.

    Raises:
        HTTPException: If the identifier is not found.
    """
    logger.info("Retrieving status for task ID: %s", identifier)
    status = get_task_status_from_db(identifier, session)

    if status is not None:
        logger.info("Status retrieved for task ID: %s", identifier)
        return status
    else:
        logger.error("Task ID not found: %s", identifier)
        raise HTTPException(status_code=404, detail="Identifier not found")


@task_router.get("/task/{identifier}/{output_format}", tags=["Tasks Management"], response_class=PlainTextResponse)
async def get_transcription_result(
    identifier: str,
    output_format: str,
    highlight_words: bool = False,
    max_line_width: int = None,
    max_line_count: int = None,
    session: Session = Depends(get_db_session),
):
    """
    Retrieve the result of certain format.

    Args:
        identifier (str): The identifier of the task.
        output_format (str): Result format what whisperx supports, which includes txt, tsv, srt, vtt, json.
        highlight_words (bool): Underline each word as it is spoken in srt and vtt.
        max_line_width (int): The maximum number of characters in a line before breaking the line.
        max_line_count (int): The maximum number of lines in a segment.
        session (Session): Database session dependency.

    Returns:
        Result of specified output format.

    Raises:
        HTTPException: If the task is not found.
    """
    logger.info("Retrieving status for task ID: %s", identifier)
    options = {"highlight_words": highlight_words, "max_line_width": max_line_width, "max_line_count": max_line_count }
    result = get_task_result_from_db(identifier, output_format, options, session)
    if result is not None:
        logger.info("Status retrieved for task ID: %s", identifier)
        return result
    else:
        logger.error("Task ID not found: %s", identifier)
        raise HTTPException(status_code=404, detail="Identifier not found")


@task_router.delete("/task/{identifier}/delete", tags=["Tasks Management"])
async def delete_task(
    identifier: str,
    session: Session = Depends(get_db_session),
) -> Response:
    """
    Delete a specific task by its identifier.

    Args:
        identifier (str): The identifier of the task.
        session (Session): Database session dependency.

    Returns:
        Response: Confirmation message of task deletion.

    Raises:
        HTTPException: If the task is not found.
    """
    logger.info("Deleting task ID: %s", identifier)
    if delete_task_from_db(identifier, session):
        logger.info("Task deleted: ID %s", identifier)
        return Response(identifier=identifier, message="Task deleted")
    else:
        logger.error("Task not found: ID %s", identifier)
        raise HTTPException(status_code=404, detail="Task not found")
