"""
Management command to seed default roles for all tenants.
"""

from django.core.management.base import BaseCommand

from modules.users.models import Role, Tenant


class Command(BaseCommand):
    help = "Create default roles (Admin, Instructor, Student) for all tenants"

    DEFAULT_ROLES = [
        {
            "name": Role.ADMIN,
            "description": "Full access to tenant resources and user management",
            "permissions": [
                "manage_users",
                "manage_roles",
                "manage_courses",
                "manage_assessments",
                "view_analytics",
                "manage_settings",
            ],
        },
        {
            "name": Role.INSTRUCTOR,
            "description": "Create and manage courses, assessments, and grade students",
            "permissions": [
                "create_courses",
                "manage_own_courses",
                "create_assessments",
                "grade_submissions",
                "view_student_progress",
                "issue_certificates",
            ],
        },
        {
            "name": Role.STUDENT,
            "description": "Enroll in courses and submit assessments",
            "permissions": [
                "enroll_courses",
                "view_courses",
                "submit_assessments",
                "view_own_progress",
                "view_certificates",
            ],
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-id",
            type=int,
            help="Seed roles for a specific tenant ID only",
        )

    def handle(self, *args, **options):
        tenant_id = options.get("tenant_id")

        if tenant_id:
            tenants = Tenant.objects.filter(id=tenant_id)
            if not tenants.exists():
                self.stdout.write(
                    self.style.ERROR(f"Tenant with ID {tenant_id} not found")
                )
                return
        else:
            tenants = Tenant.objects.all()

        total_created = 0

        for tenant in tenants:
            created_count = self._seed_roles_for_tenant(tenant)
            total_created += created_count

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {total_created} default roles "
                f"across {tenants.count()} tenant(s)"
            )
        )

    def _seed_roles_for_tenant(self, tenant):
        created_count = 0

        for role_data in self.DEFAULT_ROLES:
            role, created = Role.objects.get_or_create(
                name=role_data["name"],
                tenant=tenant,
                defaults={
                    "description": role_data["description"],
                    "permissions": role_data["permissions"],
                    "is_system_role": True,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created {role.get_name_display()} "
                        f"role for {tenant.name}"
                    )
                )
            else:
                self.stdout.write(
                    f"  {role.get_name_display()} role "
                    f"already exists for {tenant.name}"
                )

        return created_count
