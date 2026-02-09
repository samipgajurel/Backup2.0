import csv
import secrets
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User

def _clean(s: str) -> str:
    return (s or "").strip()

def _norm_key(s: str) -> str:
    s = _clean(s).lower()
    s = s.replace(":", "").replace(".", "").replace("_", " ")
    s = " ".join(s.split())
    return s

def _role_from_header_cell(cell: str) -> str | None:
    c = _clean(cell).lower()
    if c.startswith("supervisor"):
        return "SUPERVISOR"
    if c.startswith("intern"):
        return "INTERN"
    if c.startswith("admin"):
        return "ADMIN"
    return None

def _create_user_from_block(block: dict, role: str, stdout):
    email = _clean(block.get("email", "")).lower()
    if not email:
        return None, "skipped(no email)"

    full_name = _clean(block.get("name", "")) or email.split("@")[0]
    employee_id = _clean(block.get("id info", "")) or _clean(block.get("employee id", ""))
    department = _clean(block.get("position", "")) or _clean(block.get("department", ""))

    if User.objects.filter(email=email).exists():
        return None, "skipped(exists)"

    password = secrets.token_urlsafe(8)

    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        role=role,
        employee_id=employee_id,
        department=department,
        is_verified=True,  # CSV-provisioned users are verified
    )

    # Print creds like your screenshot
    stdout.write(f"{email} | {password} | {employee_id or '-'} | {department or '-'}")
    return user, "created"

class Command(BaseCommand):
    help = "Import users from the Codavatar CSV (block-style + tabular). Prints generated credentials."

    def add_arguments(self, parser):
        parser.add_argument("--path", required=True, help="Path to CSV file")
        parser.add_argument("--dry-run", action="store_true", help="Parse only, do not write DB")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = Path(opts["path"])
        if not path.exists():
            self.stderr.write(f"File not found: {path}")
            return

        dry = opts["dry_run"]

        # Read as raw rows
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            rows = list(csv.reader(f))

        created = 0
        skipped = 0

        # -------------- 1) BLOCK MODE (Supervisor/Intern blocks) --------------
        role = None
        block = {}

        def flush_block():
            nonlocal created, skipped, block, role
            if not role:
                block = {}
                return
            if not block:
                return

            if dry:
                self.stdout.write(f"[DRY] {role} block -> {block}")
                block = {}
                return

            user, status = _create_user_from_block(block, role, self.stdout)
            if status.startswith("created"):
                created += 1
            else:
                skipped += 1
            block = {}

        for r in rows:
            if not r:
                continue

            first = _clean(r[0])
            if not first:
                continue

            # detect role line: "Supervisor ,,,,,,,"
            new_role = _role_from_header_cell(first)
            if new_role:
                flush_block()
                role = new_role
                block = {}
                continue

            # detect key,value lines: "Name: ,Samip Gajurel"
            if len(r) >= 2:
                k = _norm_key(r[0])
                v = _clean(r[1])
                if k in {"name", "email", "id info", "position", "department", "employee id"}:
                    if v:
                        block[k] = v

        flush_block()

        # -------------- 2) TABULAR MODE (normal table with headers) --------------
        # find header row containing email column
        header_idx = None
        for i, r in enumerate(rows):
            joined = " ".join([_clean(x).lower() for x in r])
            if "e-mail" in joined or "email" in joined:
                header_idx = i
                break

        if header_idx is not None:
            # rebuild DictReader from that point onward
            text_lines = []
            for r in rows[header_idx:]:
                text_lines.append(",".join([x.replace(",", " ") for x in r]))

            dict_reader = csv.DictReader(text_lines)
            for row in dict_reader:
                email = (_clean(row.get("E-mail")) or _clean(row.get("Email"))).lower()
                if not email:
                    continue
                if User.objects.filter(email=email).exists():
                    skipped += 1
                    continue

                role_raw = _clean(row.get("Role", "")).lower()
                if "supervisor" in role_raw:
                    role2 = "SUPERVISOR"
                elif "admin" in role_raw:
                    role2 = "ADMIN"
                else:
                    role2 = "INTERN"

                full_name = _clean(row.get("Intern Name") or row.get("Name") or email.split("@")[0])
                employee_id = _clean(row.get("ID Info") or row.get("Employee ID") or "")
                department = _clean(row.get("Department") or "")

                password = secrets.token_urlsafe(8)

                if dry:
                    self.stdout.write(f"[DRY] {email} role={role2}")
                    continue

                User.objects.create_user(
                    email=email,
                    password=password,
                    full_name=full_name,
                    role=role2,
                    employee_id=employee_id,
                    department=department,
                    is_verified=True,
                )
                created += 1
                self.stdout.write(f"{email} | {password} | {employee_id or '-'} | {department or '-'}")

        self.stdout.write(self.style.SUCCESS(f"Done. created={created}, skipped={skipped}"))
        if dry:
            self.stdout.write("DRY RUN: no DB changes were committed.")
