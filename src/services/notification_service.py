import logging

logger = logging.getLogger("gold_tier")


class NotificationService:
    def send_approval_required(self, plan_id: str, approver_emails: list[str]):
        logger.info(f"[NOTIFICATION] Approval required for plan {plan_id} -> {approver_emails}")

    def send_plan_approved(self, plan_id: str, submitter_email: str):
        logger.info(f"[NOTIFICATION] Plan {plan_id} approved -> {submitter_email}")

    def send_plan_rejected(self, plan_id: str, submitter_email: str, comments: str):
        logger.info(f"[NOTIFICATION] Plan {plan_id} rejected -> {submitter_email}")

    def send_job_completed(self, job_id: str, submitter_email: str):
        logger.info(f"[NOTIFICATION] Job {job_id} completed -> {submitter_email}")

    def send_job_failed(self, job_id: str, submitter_email: str, error: str):
        logger.info(f"[NOTIFICATION] Job {job_id} failed -> {submitter_email}")
