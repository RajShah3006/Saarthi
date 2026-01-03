# controllers.py - Thin handlers that delegate to services

import logging
import traceback
import json
import re
from typing import Tuple, List, Any

import gradio as gr

from config import Config
from models import StudentProfile
from services.session import SessionManager
from services.program_search import ProgramSearchService
from services.roadmap import RoadmapService
from services.llm_client import LLMClient
from utils.validators import Validators

logger = logging.getLogger("saarthi.controllers")


DATA_MARKER_RE = re.compile(r"<!--SAARTHI_DATA:(.+?)-->", re.DOTALL)


class Controllers:
    """Thin controller layer - validates input, calls services, formats output"""

    def __init__(self, config: Config):
        self.config = config

        # Services
        self.session_manager = SessionManager(config)
        self.program_search = ProgramSearchService(config)
        self.llm_client = LLMClient(config)
        self.roadmap_service = RoadmapService(config, self.llm_client, self.program_search)

        # Validation
        self.validators = Validators(config)

    def wire_events(self, components: dict, render_roadmap_bundle):
        """Wire UI events to handlers"""

        # Unpack inputs
        name_input = components["inputs"]["name_input"]
        interest_input = components["inputs"]["interest_input"]
        grade_input = components["inputs"]["grade_input"]
        average_input = components["inputs"]["average_input"]
        subjects_input = components["inputs"]["subjects_input"]
        location_input = components["inputs"]["location_input"]
        budget_input = components["inputs"]["budget_input"]

        # Outputs (dashboard panels)
        timeline_display = components["outputs"]["timeline_display"]
        programs_display = components["outputs"]["programs_display"]
        checklist_display = components["outputs"]["checklist_display"]
        output_display = components["outputs"]["output_display"]

        followup_input = components["outputs"]["followup_input"]
        send_btn = components["outputs"]["send_btn"]

        def on_generate(name, interest, grade, average, subjects, location, budget):
            try:
                # Validate / normalize
                vr = self.validators.validate_profile(
                    name=name,
                    interest=interest,
                    grade=grade,
                    average=average,
                    subjects=subjects,
                    location=location,
                    budget=budget
                )
                if not vr.ok:
                    return ("", "", "", vr.message, "", gr.update(visible=False))

                profile: StudentProfile = vr.data

                # Create session
                session = self.session_manager.create_session(profile.name)

                # Generate roadmap (markdown)
                rr = self.roadmap_service.generate(profile, session)
                if not rr.ok:
                    return ("", "", "", rr.message, "", gr.update(visible=False))

                md = rr.data  # markdown string

                # Render into dashboard blocks
                bundle = render_roadmap_bundle(md)

                return (
                    bundle.get("timeline", ""),
                    bundle.get("programs", ""),
                    bundle.get("checklist", ""),
                    bundle.get("full", ""),
                    "",
                    gr.update(visible=True)
                )

            except Exception as e:
                logger.error(f"Generate error: {e}")
                logger.error(traceback.format_exc())
                return ("", "", "", f"❌ Error: {e}", "", gr.update(visible=False))

        def on_followup(question, current_full_md):
            try:
                if not question or not question.strip():
                    return gr.update(value=""), current_full_md

                # Send followup to LLM with context (full markdown)
                fr = self.llm_client.followup(question.strip(), current_full_md or "")
                if not fr.ok:
                    return gr.update(value=""), current_full_md

                new_md = fr.data

                return gr.update(value=""), new_md

            except Exception as e:
                logger.error(f"Followup error: {e}")
                logger.error(traceback.format_exc())
                return gr.update(value=""), current_full_md

        # Generate button
        components["actions"]["generate_btn"].click(
            fn=on_generate,
            inputs=[name_input, interest_input, grade_input, average_input, subjects_input, location_input, budget_input],
            outputs=[timeline_display, programs_display, checklist_display, output_display, followup_input, send_btn]
        )

        # Followup button
        send_btn.click(
            fn=on_followup,
            inputs=[followup_input, output_display],
            outputs=[followup_input, output_display]
        )

    @staticmethod
    def extract_marker_payload(md: str) -> dict:
        """Extract embedded JSON marker from markdown (if present)."""
        m = DATA_MARKER_RE.search(md or "")
        if not m:
            return {}
        raw = m.group(1)
        try:
            return json.loads(raw)
        except Exception:
            return {}

    @staticmethod
    def _minimize_program(p: Any) -> dict:
        """Reduce Program object/dict to JSON-safe minimal payload."""
        try:
            if hasattr(p, "__dict__"):
                d = dict(p.__dict__)
            elif isinstance(p, dict):
                d = dict(p)
            else:
                return {"program_name": str(p)}

            # Remove huge fields
            d.pop("embedding", None)
            d.pop("raw", None)

            # Make sure any numpy floats are JSON-safe
            for k, v in list(d.items()):
                if hasattr(v, "item"):
                    try:
                        d[k] = v.item()
                    except Exception:
                        pass
            return d
        except Exception:
            return {"program_name": str(p)}
