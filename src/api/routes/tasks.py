"""Vault-based Tasks router for Dashboard."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.api.response import api_response
from src.api.vault_utils import read_vault_folder, move_vault_file

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("/pending")
async def get_pending_tasks():
    """Tasks in Pending_Approval."""
    return api_response(read_vault_folder("Pending_Approval"))

@router.get("/needs-action")
async def get_needs_action_tasks():
    """Tasks in Needs_Action."""
    return api_response(read_vault_folder("Needs_Action"))

@router.get("/done")
async def get_done_tasks():
    """Tasks in Done."""
    return api_response(read_vault_folder("Done"))

@router.get("/plans")
async def get_plans():
    """Task plans in /Plans."""
    return api_response(read_vault_folder("Plans"))
