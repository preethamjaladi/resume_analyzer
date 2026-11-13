"""Run with: python -m resume_analyzer.main resume.txt job_description.txt"""

from .graph import workflow_graph

def main():
    resume = """ALEX MORGAN
Software Engineer
Newark, NJ
alex.morgan@example.com
linkedin.com/in/alex-morgan-example
github.com/alex-morgan-example

PROFESSIONAL SUMMARY

Software Engineer with hands-on experience designing and developing
backend services, RESTful APIs, and responsive web applications.
Experienced in Python, FastAPI, PostgreSQL, React, JavaScript, and
Docker. Comfortable with Git-based collaboration, automated
testing, relational databases, and debugging production issues.
Interested in building reliable, scalable software systems.

TECHNICAL SKILLS

Languages:
Python, JavaScript, TypeScript, SQL, Java

Backend:
FastAPI, Flask, RESTful APIs, Node.js, Express.js

Frontend:
React.js, HTML5, CSS3, Tailwind CSS

Databases:
PostgreSQL, MySQL, Redis

Tools:
Git, GitHub, Docker, Postman, Pytest, GitHub Actions

Concepts:
Object-Oriented Programming, Data Structures and Algorithms,
Database Design, Authentication, Unit Testing, CI/CD,
Agile Development, API Integration

PROFESSIONAL EXPERIENCE

Software Engineer Intern
BrightPath Technologies | Newark, NJ
January 2025 – August 2025

- Developed RESTful API endpoints using Python, FastAPI, and
  PostgreSQL for an internal employee management platform.
- Designed relational database schemas and optimized SQL queries
  to improve API response times by approximately 20%.
- Implemented authentication and role-based access control
  for employee and administrator workflows.
- Developed reusable React components and integrated frontend
  interfaces with backend REST APIs.
- Wrote unit tests using Pytest and participated in code reviews.
- Containerized backend applications using Docker.
- Collaborated with four developers using Git, GitHub pull
  requests, and Agile sprint planning.
- Investigated and resolved API validation errors and
  database transaction issues.

Junior Web Developer
BlueOak Digital | Remote
June 2024 – December 2024

- Developed web applications using JavaScript, React, and Node.js.
- Built and maintained REST API integrations for customer
  dashboards and internal administration tools.
- Designed MySQL database tables and implemented CRUD operations.
- Fixed frontend bugs, improved form validation, and
  maintained reusable UI components.
- Used Git for version control and collaborated with
  designers and developers on feature releases.

PROJECTS

1. Intelligent Job Application Tracker
Python, FastAPI, PostgreSQL, React, Docker

- Developed a full-stack job tracking application supporting
  application management, status updates, and analytics.
- Implemented REST APIs for creating, updating, and retrieving
  job application records.
- Used PostgreSQL for relational data storage and SQL queries.
- Built a React dashboard to display application statistics.
- Containerized the backend with Docker.

2. AI-Powered Document Question Answering
Python, LangChain, OpenAI API, FAISS, Streamlit

- Built a retrieval-augmented generation application that
  answers questions using uploaded documents.
- Implemented document chunking, text embeddings, and
  similarity-based retrieval.
- Integrated an LLM API to generate answers using
  retrieved document context.
- Developed a basic evaluation script for response relevance.

3. E-Commerce Inventory Management System
Java, Spring Boot, MySQL

- Developed backend services for inventory tracking,
  product management, and order processing.
- Implemented REST endpoints and CRUD operations.
- Used MySQL for relational data storage.
- Implemented input validation and exception handling.

EDUCATION

Bachelor of Science in Computer Science
Garden State University | Newark, NJ
September 2020 – May 2024

Relevant Coursework:
Data Structures and Algorithms, Database Management Systems,
Operating Systems, Computer Networks, Software Engineering,
Object-Oriented Programming

CERTIFICATIONS

None listed.

LANGUAGES

English - Fluent
Spanish - Basic conversational proficiency"""


    job_description = """BACKEND SOFTWARE ENGINEER
Company: Northstar Digital Systems
Location: Jersey City, NJ
Employment Type: Full-Time
Experience Level: Entry-Level / Early Career

ABOUT THE COMPANY

Northstar Digital Systems develops cloud-based software
platforms for businesses managing customers, transactions,
and operational workflows.

We are seeking a Backend Software Engineer to help build,
maintain, and improve reliable software services.

RESPONSIBILITIES

- Design, develop, and maintain backend services using
  Python and modern web frameworks.
- Build RESTful APIs that integrate with frontend
  applications and third-party services.
- Design relational database schemas and write efficient
  SQL queries.
- Develop unit and integration tests to maintain software
  reliability.
- Debug application issues, investigate production errors,
  and implement fixes.
- Collaborate with frontend engineers, QA, and product teams.
- Participate in code reviews and maintain technical
  documentation.
- Support containerized application deployments and CI/CD.
- Work with senior engineers to improve system performance.

REQUIRED QUALIFICATIONS

1. Bachelor's degree in Computer Science, Software
   Engineering, or a related technical field.

2. At least 2 years of professional software development
   experience, including internships or paid employment.

3. Strong programming skills in Python.

4. Hands-on experience developing RESTful APIs using
   FastAPI, Flask, or a comparable framework.

5. Experience working with SQL and relational databases,
   preferably PostgreSQL or MySQL.

6. Experience using Git for version control.

7. Familiarity with unit testing and automated
   testing frameworks such as Pytest.

8. Experience using Docker for containerizing applications.

9. Understanding of data structures, algorithms,
   and object-oriented programming.

10. Experience debugging backend services and
    investigating application errors.

11. Professional working proficiency in English.

PREFERRED QUALIFICATIONS

1. Experience with AWS services such as EC2, S3,
   Lambda, or RDS.

2. Familiarity with Kubernetes and container orchestration.

3. Experience developing applications using React
   or TypeScript.

4. Familiarity with CI/CD pipelines and GitHub Actions.

5. Experience working with Redis or other caching tools.

6. Familiarity with distributed systems and
   microservices architecture.

7. Experience with GraphQL APIs.

8. AWS Certified Developer - Associate certification.

9. Professional working proficiency in Mandarin Chinese.

ADDITIONAL INFORMATION

Candidates should demonstrate practical engineering
experience, problem-solving ability, and the ability to
collaborate effectively with other developers.

We value candidates who can learn new technologies
quickly and communicate technical decisions clearly."""

    result = workflow_graph.invoke({
        "resume": resume,
        "job_description": job_description
    })

    print("Match Score:", result["match_score"])
    print("Hard Gaps:", result["hard_gaps"])

    #tempcode
    for match in result["requirement_matches"]:
        print(
            match.requirement_id,
            "|", match.status,
            "|", match.evidence
        )

    for verification in result["verification_results"]:
        print(
            verification.requirement_id,
        "|", verification.status,
        "|", verification.explanation
    )

if __name__ == "__main__":
    main()