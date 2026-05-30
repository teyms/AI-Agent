from sqlite_vec_store import (
    init_db,
    insert_document
)

conn = init_db()


documents = [
    {
        "source": "leave_policy.txt",
        "department": "HR",
        "document_type": "policy",
        "text": """
Employees receive 14 days
of annual leave.
"""
    },
    {
        "source": "remote_work.txt",
        "department": "HR",
        "document_type": "policy",
        "text": """
Employees may work remotely
up to 3 days per week.
"""
    },
    {
        "source": "engineering_handbook.txt",
        "department": "Engineering",
        "document_type": "handbook",
        "text": """
Engineering pull requests require review,
focused tests, and passing builds before deployment.
"""
    },
    {
        "source": "faq_docs.txt",
        "department": "HR",
        "document_type": "faq",
        "text": """
Employees get 14 days of annual leave per year.
Remote work is allowed up to 3 days per week.
"""
    },
    {
        "source": "onboarding_docs.txt",
        "department": "General",
        "document_type": "onboarding",
        "text": """
New employees should set up accounts,
complete training, and pair with an onboarding buddy.
"""
    }
]


for doc in documents:

    insert_document(
        conn,
        doc["text"],
        doc["source"],
        doc["department"],
        doc["document_type"]
    )

print("Documents ingested.")





