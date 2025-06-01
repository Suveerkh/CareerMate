# career_test.py
# Career Fit Test implementation for CareerMate

import os
import json
import datetime
import uuid
import random
from flask import session

# Career test questions organized by category
CAREER_TEST_QUESTIONS = {
    "personality": [
        {
            "id": "p1",
            "text": "I enjoy solving complex problems and puzzles.",
            "trait": "analytical"
        },
        {
            "id": "p2",
            "text": "I prefer working in teams rather than independently.",
            "trait": "collaborative"
        },
        {
            "id": "p3",
            "text": "I am comfortable taking risks and trying new approaches.",
            "trait": "innovative"
        },
        {
            "id": "p4",
            "text": "I enjoy helping others solve their problems.",
            "trait": "supportive"
        },
        {
            "id": "p5",
            "text": "I prefer having a structured routine rather than variety in my day.",
            "trait": "structured"
        },
        {
            "id": "p6",
            "text": "I enjoy being in leadership positions.",
            "trait": "leadership"
        },
        {
            "id": "p7",
            "text": "I am detail-oriented and notice things others might miss.",
            "trait": "detail_oriented"
        },
        {
            "id": "p8",
            "text": "I prefer creative tasks over technical ones.",
            "trait": "creative"
        },
        {
            "id": "p9",
            "text": "I am comfortable speaking in front of groups.",
            "trait": "outgoing"
        },
        {
            "id": "p10",
            "text": "I enjoy analyzing data and finding patterns.",
            "trait": "analytical"
        }
    ],
    "interests": [
        {
            "id": "i1",
            "text": "I enjoy working with computers and technology.",
            "field": "technology"
        },
        {
            "id": "i2",
            "text": "I am interested in business, finance, and economics.",
            "field": "business"
        },
        {
            "id": "i3",
            "text": "I enjoy helping people with their health and wellbeing.",
            "field": "healthcare"
        },
        {
            "id": "i4",
            "text": "I am interested in teaching and sharing knowledge.",
            "field": "education"
        },
        {
            "id": "i5",
            "text": "I enjoy creative activities like writing, design, or art.",
            "field": "creative"
        },
        {
            "id": "i6",
            "text": "I am interested in how society works and social issues.",
            "field": "social_sciences"
        },
        {
            "id": "i7",
            "text": "I enjoy building or fixing things with my hands.",
            "field": "trades"
        },
        {
            "id": "i8",
            "text": "I am interested in science and scientific research.",
            "field": "science"
        },
        {
            "id": "i9",
            "text": "I enjoy organizing events or managing projects.",
            "field": "management"
        },
        {
            "id": "i10",
            "text": "I am interested in law, politics, or public policy.",
            "field": "legal_policy"
        }
    ],
    "skills": [
        {
            "id": "s1",
            "text": "I am good at logical reasoning and problem-solving.",
            "skill": "problem_solving"
        },
        {
            "id": "s2",
            "text": "I communicate effectively in writing.",
            "skill": "written_communication"
        },
        {
            "id": "s3",
            "text": "I am skilled at analyzing data and statistics.",
            "skill": "data_analysis"
        },
        {
            "id": "s4",
            "text": "I am good at persuading others and negotiating.",
            "skill": "persuasion"
        },
        {
            "id": "s5",
            "text": "I have strong technical or programming abilities.",
            "skill": "technical"
        },
        {
            "id": "s6",
            "text": "I am skilled at managing my time and staying organized.",
            "skill": "organization"
        },
        {
            "id": "s7",
            "text": "I am good at creative thinking and generating new ideas.",
            "skill": "creativity"
        },
        {
            "id": "s8",
            "text": "I have strong research and information-gathering skills.",
            "skill": "research"
        },
        {
            "id": "s9",
            "text": "I am skilled at managing and resolving conflicts.",
            "skill": "conflict_resolution"
        },
        {
            "id": "s10",
            "text": "I adapt quickly to new technologies and tools.",
            "skill": "adaptability"
        }
    ],
    "values": [
        {
            "id": "v1",
            "text": "Having work-life balance is important to me.",
            "value": "work_life_balance"
        },
        {
            "id": "v2",
            "text": "I value financial stability and high earning potential.",
            "value": "financial_security"
        },
        {
            "id": "v3",
            "text": "Making a positive impact on society is important to me.",
            "value": "social_impact"
        },
        {
            "id": "v4",
            "text": "I value recognition and status in my career.",
            "value": "recognition"
        },
        {
            "id": "v5",
            "text": "Having autonomy and independence in my work is important.",
            "value": "autonomy"
        },
        {
            "id": "v6",
            "text": "I value job security and stability.",
            "value": "job_security"
        },
        {
            "id": "v7",
            "text": "Continuous learning and growth are important to me.",
            "value": "growth"
        },
        {
            "id": "v8",
            "text": "I value creativity and self-expression in my work.",
            "value": "creativity"
        },
        {
            "id": "v9",
            "text": "Building relationships and working with others is important.",
            "value": "relationships"
        },
        {
            "id": "v10",
            "text": "I value challenging work that pushes my abilities.",
            "value": "challenge"
        }
    ]
}

# Career profiles with trait mappings
CAREER_PROFILES = {
    "data-scientist": {
        "title": "Data Scientist",
        "category": "technology",
        "traits": {
            "analytical": 0.9,
            "detail_oriented": 0.8,
            "innovative": 0.7,
            "collaborative": 0.6,
            "structured": 0.7
        },
        "skills": {
            "problem_solving": 0.9,
            "data_analysis": 0.9,
            "technical": 0.8,
            "research": 0.7,
            "adaptability": 0.6
        },
        "values": {
            "growth": 0.8,
            "challenge": 0.8,
            "financial_security": 0.7,
            "autonomy": 0.6,
            "recognition": 0.6
        },
        "education_paths": [
            "Bachelor's in Computer Science, Statistics, or Mathematics",
            "Master's in Data Science, Machine Learning, or Analytics",
            "Online certifications in data science and machine learning"
        ],
        "skill_gaps": {
            "data_analysis": "Take courses in statistics and data analysis",
            "technical": "Learn programming languages like Python, R, and SQL",
            "problem_solving": "Practice with real-world data challenges",
            "research": "Participate in research projects or competitions"
        }
    },
    "software-engineer": {
        "title": "Software Engineer",
        "category": "technology",
        "traits": {
            "analytical": 0.8,
            "detail_oriented": 0.8,
            "innovative": 0.7,
            "collaborative": 0.7,
            "structured": 0.6
        },
        "skills": {
            "problem_solving": 0.9,
            "technical": 0.9,
            "adaptability": 0.7,
            "organization": 0.6,
            "written_communication": 0.6
        },
        "values": {
            "growth": 0.8,
            "financial_security": 0.8,
            "challenge": 0.7,
            "autonomy": 0.7,
            "work_life_balance": 0.6
        },
        "education_paths": [
            "Bachelor's in Computer Science or Software Engineering",
            "Coding bootcamps for specific technologies",
            "Online certifications in programming languages and frameworks"
        ],
        "skill_gaps": {
            "technical": "Learn programming languages and frameworks",
            "problem_solving": "Practice algorithmic problem solving",
            "organization": "Learn software development methodologies",
            "adaptability": "Stay updated with new technologies"
        }
    },
    "web-developer": {
        "title": "Web Developer",
        "category": "technology",
        "traits": {
            "creative": 0.8,
            "detail_oriented": 0.7,
            "innovative": 0.7,
            "collaborative": 0.6,
            "adaptability": 0.8
        },
        "skills": {
            "technical": 0.8,
            "creativity": 0.7,
            "problem_solving": 0.7,
            "adaptability": 0.8,
            "organization": 0.6
        },
        "values": {
            "creativity": 0.8,
            "autonomy": 0.7,
            "growth": 0.7,
            "work_life_balance": 0.7,
            "financial_security": 0.6
        },
        "education_paths": [
            "Bachelor's in Web Development or Computer Science",
            "Web development bootcamps",
            "Online courses in HTML, CSS, JavaScript, and frameworks"
        ],
        "skill_gaps": {
            "technical": "Learn HTML, CSS, JavaScript, and frameworks",
            "creativity": "Build a portfolio of web projects",
            "adaptability": "Stay updated with web technologies",
            "problem_solving": "Practice debugging and optimization"
        }
    },
    "cybersecurity-analyst": {
        "title": "Cybersecurity Analyst",
        "category": "technology",
        "traits": {
            "analytical": 0.9,
            "detail_oriented": 0.9,
            "structured": 0.7,
            "innovative": 0.6,
            "supportive": 0.6
        },
        "skills": {
            "technical": 0.8,
            "problem_solving": 0.8,
            "research": 0.7,
            "adaptability": 0.7,
            "organization": 0.7
        },
        "values": {
            "job_security": 0.8,
            "challenge": 0.8,
            "financial_security": 0.7,
            "growth": 0.7,
            "social_impact": 0.6
        },
        "education_paths": [
            "Bachelor's in Cybersecurity or Computer Science",
            "Certifications like CompTIA Security+, CISSP, or CEH",
            "Specialized courses in network security and ethical hacking"
        ],
        "skill_gaps": {
            "technical": "Learn security tools and technologies",
            "research": "Stay updated with security threats and vulnerabilities",
            "problem_solving": "Practice with security challenges and CTFs",
            "adaptability": "Keep up with evolving security landscape"
        }
    },
    "management-consultant": {
        "title": "Management Consultant",
        "category": "business",
        "traits": {
            "analytical": 0.8,
            "leadership": 0.8,
            "outgoing": 0.7,
            "innovative": 0.7,
            "collaborative": 0.7
        },
        "skills": {
            "problem_solving": 0.9,
            "persuasion": 0.8,
            "written_communication": 0.8,
            "data_analysis": 0.7,
            "organization": 0.7
        },
        "values": {
            "financial_security": 0.9,
            "challenge": 0.8,
            "recognition": 0.7,
            "growth": 0.7,
            "relationships": 0.6
        },
        "education_paths": [
            "Bachelor's in Business, Economics, or related field",
            "MBA or Master's in Management",
            "Certifications in project management or specific industries"
        ],
        "skill_gaps": {
            "problem_solving": "Develop case study analysis skills",
            "persuasion": "Improve presentation and communication skills",
            "data_analysis": "Learn business analytics tools",
            "organization": "Develop project management skills"
        }
    },
    "financial-analyst": {
        "title": "Financial Analyst",
        "category": "business",
        "traits": {
            "analytical": 0.9,
            "detail_oriented": 0.9,
            "structured": 0.8,
            "collaborative": 0.6,
            "leadership": 0.5
        },
        "skills": {
            "data_analysis": 0.9,
            "problem_solving": 0.8,
            "research": 0.7,
            "written_communication": 0.7,
            "technical": 0.6
        },
        "values": {
            "financial_security": 0.9,
            "job_security": 0.7,
            "growth": 0.7,
            "challenge": 0.7,
            "recognition": 0.6
        },
        "education_paths": [
            "Bachelor's in Finance, Economics, or Accounting",
            "Master's in Finance or MBA",
            "CFA (Chartered Financial Analyst) certification"
        ],
        "skill_gaps": {
            "data_analysis": "Learn financial modeling and analysis tools",
            "technical": "Develop skills in Excel and financial software",
            "research": "Practice financial research and valuation",
            "written_communication": "Improve financial reporting skills"
        }
    },
    "physician": {
        "title": "Physician",
        "category": "healthcare",
        "traits": {
            "detail_oriented": 0.9,
            "analytical": 0.8,
            "supportive": 0.8,
            "structured": 0.7,
            "leadership": 0.6
        },
        "skills": {
            "problem_solving": 0.9,
            "research": 0.8,
            "communication": 0.8,
            "adaptability": 0.7,
            "conflict_resolution": 0.7
        },
        "values": {
            "social_impact": 0.9,
            "financial_security": 0.8,
            "recognition": 0.7,
            "growth": 0.7,
            "challenge": 0.8
        },
        "education_paths": [
            "Bachelor's degree (pre-med)",
            "Medical school (MD or DO)",
            "Residency and possibly fellowship",
            "Board certification"
        ],
        "skill_gaps": {
            "problem_solving": "Develop clinical reasoning skills",
            "research": "Participate in medical research",
            "communication": "Practice patient communication",
            "adaptability": "Stay updated with medical advances"
        }
    },
    "professor": {
        "title": "Professor",
        "category": "education",
        "traits": {
            "analytical": 0.8,
            "outgoing": 0.7,
            "detail_oriented": 0.8,
            "innovative": 0.7,
            "leadership": 0.6
        },
        "skills": {
            "research": 0.9,
            "written_communication": 0.9,
            "problem_solving": 0.7,
            "creativity": 0.7,
            "organization": 0.7
        },
        "values": {
            "autonomy": 0.9,
            "growth": 0.8,
            "social_impact": 0.8,
            "work_life_balance": 0.7,
            "job_security": 0.7
        },
        "education_paths": [
            "Bachelor's degree in field of interest",
            "Master's degree in specialized area",
            "PhD in academic discipline",
            "Post-doctoral research (in some fields)"
        ],
        "skill_gaps": {
            "research": "Develop research methodology skills",
            "written_communication": "Practice academic writing",
            "creativity": "Develop innovative teaching methods",
            "organization": "Learn course development and management"
        }
    }
}


def get_test_questions(plan_type="free"):
    """
    Return test questions organized by category, limited by plan type

    Args:
        plan_type: "free" or "premium"

    Returns:
        Dictionary of questions by category
    """
    # Define question limits based on plan
    if plan_type == "premium":
        question_limit = 60  # Premium users get all questions
    else:
        question_limit = 20  # Free users get limited questions

    # Create a copy of the questions dictionary
    limited_questions = {}

    # Track total questions added
    total_questions = 0

    # Calculate questions per category
    categories = list(CAREER_TEST_QUESTIONS.keys())
    questions_per_category = question_limit // len(categories)

    # Add questions from each category
    for category in categories:
        category_questions = CAREER_TEST_QUESTIONS[category]

        # Limit questions for this category
        if plan_type == "premium":
            limited_questions[category] = category_questions
        else:
            # For free plan, take a subset of questions
            limited_questions[category] = category_questions[:questions_per_category]
            total_questions += questions_per_category

    return limited_questions


def calculate_career_matches(answers, plan_type="free"):
    """
    Calculate career matches based on test answers

    Args:
        answers: Dictionary of question IDs and their scores (1-5)
        plan_type: "free" or "premium"

    Returns:
        List of career matches with scores and insights, limited by plan type
    """
    # Initialize trait scores
    trait_scores = {}

    # Process answers to calculate trait scores
    for question_id, score in answers.items():
        # Normalize score to 0-1 range
        normalized_score = (int(score) - 1) / 4.0

        # Find the question and its associated trait
        for category in CAREER_TEST_QUESTIONS:
            for question in CAREER_TEST_QUESTIONS[category]:
                if question["id"] == question_id:
                    trait_type = None
                    trait_name = None

                    if category == "personality":
                        trait_type = "traits"
                        trait_name = question["trait"]
                    elif category == "interests":
                        trait_type = "interests"
                        trait_name = question["field"]
                    elif category == "skills":
                        trait_type = "skills"
                        trait_name = question["skill"]
                    elif category == "values":
                        trait_type = "values"
                        trait_name = question["value"]

                    if trait_type and trait_name:
                        if trait_type not in trait_scores:
                            trait_scores[trait_type] = {}

                        if trait_name not in trait_scores[trait_type]:
                            trait_scores[trait_type][trait_name] = []

                        trait_scores[trait_type][trait_name].append(normalized_score)

    # Average the scores for each trait
    for trait_type in trait_scores:
        for trait_name in trait_scores[trait_type]:
            scores = trait_scores[trait_type][trait_name]
            trait_scores[trait_type][trait_name] = sum(scores) / len(scores)

    # Calculate match scores for each career
    career_matches = []

    for career_id, career in CAREER_PROFILES.items():
        # Initialize match components
        trait_match = 0
        trait_count = 0
        skill_match = 0
        skill_count = 0
        value_match = 0
        value_count = 0

        # Calculate trait match
        if "traits" in trait_scores and "traits" in career:
            for trait, career_value in career["traits"].items():
                if trait in trait_scores["traits"]:
                    trait_match += (1 - abs(career_value - trait_scores["traits"][trait])) * career_value
                    trait_count += career_value

        # Calculate skill match
        if "skills" in trait_scores and "skills" in career:
            for skill, career_value in career["skills"].items():
                if skill in trait_scores["skills"]:
                    skill_match += (1 - abs(career_value - trait_scores["skills"][skill])) * career_value
                    skill_count += career_value

        # Calculate value match
        if "values" in trait_scores and "values" in career:
            for value, career_value in career["values"].items():
                if value in trait_scores["values"]:
                    value_match += (1 - abs(career_value - trait_scores["values"][value])) * career_value
                    value_count += career_value

        # Calculate overall match percentage
        trait_score = trait_match / trait_count if trait_count > 0 else 0
        skill_score = skill_match / skill_count if skill_count > 0 else 0
        value_score = value_match / value_count if value_count > 0 else 0

        # Weight the components (can be adjusted)
        overall_match = (trait_score * 0.4) + (skill_score * 0.4) + (value_score * 0.2)
        match_percentage = round(overall_match * 100)

        # Identify strengths and gaps
        strengths = []
        gaps = []

        # Find top strengths
        for trait_type in ["traits", "skills", "values"]:
            if trait_type in trait_scores and trait_type in career:
                for item, career_value in career[trait_type].items():
                    if item in trait_scores[trait_type]:
                        user_value = trait_scores[trait_type][item]
                        if user_value >= 0.7 and career_value >= 0.7:
                            strengths.append({
                                "type": trait_type,
                                "name": item,
                                "score": user_value
                            })

        # Find top gaps
        for trait_type in ["traits", "skills", "values"]:
            if trait_type in trait_scores and trait_type in career:
                for item, career_value in career[trait_type].items():
                    if item in trait_scores[trait_type]:
                        user_value = trait_scores[trait_type][item]
                        if user_value < 0.6 and career_value >= 0.7:
                            gaps.append({
                                "type": trait_type,
                                "name": item,
                                "score": user_value,
                                "target": career_value,
                                "improvement": career["skill_gaps"].get(item,
                                                                        "Develop this skill through relevant courses and practice")
                                if trait_type == "skills" else "Focus on developing this area"
                            })

        # Sort strengths and gaps
        strengths = sorted(strengths, key=lambda x: x["score"], reverse=True)[:3]
        gaps = sorted(gaps, key=lambda x: x["target"] - x["score"], reverse=True)[:3]

        # Add career match to results
        career_matches.append({
            "id": career_id,
            "title": career["title"],
            "category": career["category"],
            "match_percentage": match_percentage,
            "trait_score": round(trait_score * 100),
            "skill_score": round(skill_score * 100),
            "value_score": round(value_score * 100),
            "strengths": strengths,
            "gaps": gaps,
            "education_paths": career["education_paths"]
        })

    # Sort career matches by match percentage
    career_matches = sorted(career_matches, key=lambda x: x["match_percentage"], reverse=True)

    # Limit results based on plan type
    if plan_type == "free":
        # Free plan gets limited career matches (top 2)
        career_matches = career_matches[:2]

        # For free plan, simplify the career matches
        for match in career_matches:
            # Simplify the career title to a more general category
            match["category_title"] = match["category"].title()

            # Limit strengths and gaps
            match["strengths"] = match["strengths"][:1] if match["strengths"] else []
            match["gaps"] = match["gaps"][:1] if match["gaps"] else []

            # Simplify education paths
            match["education_paths"] = match["education_paths"][:1] if match["education_paths"] else []
    else:
        # Premium plan gets more detailed matches (top 10)
        career_matches = career_matches[:10]

    return career_matches


def save_test_results(user_id, answers, results, personality_insights=None, plan_type="free"):
    """
    Save test results to the database

    Args:
        user_id: User ID
        answers: Dictionary of question IDs and their scores
        results: Career match results
        personality_insights: Personality insights from the test
        plan_type: "free" or "premium"

    Returns:
        Result ID and result object
    """
    # Generate a unique ID for the test result
    result_id = str(uuid.uuid4())

    # Create result object
    result = {
        "id": result_id,
        "user_id": user_id,
        "answers": answers,
        "results": results,
        "personality_insights": personality_insights,
        "plan_type": plan_type,
        "created_at": str(datetime.datetime.now())
    }

    return result_id, result


def generate_pdf_report(user_data, test_results, personality_insights):
    """
    Generate a PDF report of career test results for premium users

    Args:
        user_data: Dictionary with user information (name, email, etc.)
        test_results: Career match results
        personality_insights: Personality insights from the test

    Returns:
        Path to the generated PDF file or None if there's an error
    """
    try:
        # This is a placeholder function that would use a PDF generation library
        # like ReportLab, WeasyPrint, or pdfkit to create a PDF report

        # For demonstration purposes, we'll create a simple text file instead of a PDF
        # In a real implementation, this would generate and save a PDF file

        import os
        from datetime import datetime

        # Create a directory for reports if it doesn't exist
        reports_dir = os.path.join(os.getcwd(), "static", "reports")
        os.makedirs(reports_dir, exist_ok=True)

        # Generate a unique filename
        report_id = str(uuid.uuid4())
        report_path = os.path.join(reports_dir, f"career_report_{report_id}.txt")

        # Write the report content to a text file
        with open(report_path, "w") as f:
            f.write(f"CAREER FIT TEST REPORT\n")
            f.write(f"======================\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
            f.write(f"For: {user_data.get('username', 'User')}\n")
            f.write(f"Email: {user_data.get('email', 'N/A')}\n\n")

            f.write(f"TOP CAREER MATCHES\n")
            f.write(f"=================\n\n")
            for i, match in enumerate(test_results[:5], 1):
                title = match.get("title", match.get("category_title", "Unknown"))
                percentage = match.get("match_percentage", 0)
                f.write(f"{i}. {title}: {percentage}% Match\n")

            f.write(f"\nPERSONALITY INSIGHTS\n")
            f.write(f"===================\n\n")
            for trait, score in personality_insights.items():
                f.write(f"{trait}: {score}\n")

        return report_path
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return None


def get_personality_insights(answers, plan_type="free"):
    """
    Generate personality insights based on test answers

    Args:
        answers: Dictionary of question IDs and their scores
        plan_type: "free" or "premium"

    Returns:
        Dictionary of personality insights, limited by plan type
    """
    # Initialize trait scores
    trait_scores = {}

    # Process personality questions
    for question_id, score in answers.items():
        # Only process personality questions
        if question_id.startswith('p'):
            # Normalize score to 0-1 range
            normalized_score = (int(score) - 1) / 4.0

            # Find the question and its associated trait
            for question in CAREER_TEST_QUESTIONS["personality"]:
                if question["id"] == question_id:
                    trait = question["trait"]

                    if trait not in trait_scores:
                        trait_scores[trait] = []

                    trait_scores[trait].append(normalized_score)

    # Average the scores for each trait
    for trait in trait_scores:
        trait_scores[trait] = sum(trait_scores[trait]) / len(trait_scores[trait])

    # Define trait descriptions
    trait_descriptions = {
        "analytical": {
            "high": "You have a strong analytical mind and enjoy solving complex problems. You excel at logical thinking and data analysis.",
            "medium": "You have a balanced approach to analysis and can think logically when needed.",
            "low": "You may prefer intuitive approaches over detailed analysis. Consider developing analytical skills for certain career paths."
        },
        "collaborative": {
            "high": "You thrive in team environments and enjoy working with others. Your collaborative nature is an asset in many workplaces.",
            "medium": "You can work well in teams but also value some independence in your work.",
            "low": "You tend to prefer working independently. Consider developing teamwork skills for collaborative environments."
        },
        "innovative": {
            "high": "You have a creative and innovative mindset. You enjoy finding new solutions and thinking outside the box.",
            "medium": "You balance innovative thinking with practical approaches.",
            "low": "You tend to prefer established methods. Consider developing creative thinking for innovation-driven fields."
        },
        "supportive": {
            "high": "You have a strong desire to help others and provide support. This trait is valuable in service-oriented careers.",
            "medium": "You can be supportive when needed while maintaining focus on your own objectives.",
            "low": "You may focus more on tasks than on supporting others. Consider developing this trait for people-oriented roles."
        },
        "structured": {
            "high": "You prefer order, structure, and clear processes. You excel in environments with established procedures.",
            "medium": "You can adapt to both structured and flexible environments.",
            "low": "You prefer flexibility over rigid structure. Consider developing organizational skills for certain roles."
        },
        "leadership": {
            "high": "You have strong leadership qualities and enjoy guiding others. You're comfortable taking charge of situations.",
            "medium": "You can take leadership roles when needed but don't always seek them out.",
            "low": "You may prefer supporting roles over leadership positions. Consider developing leadership skills if interested in management."
        },
        "detail_oriented": {
            "high": "You have a keen eye for detail and thoroughness in your work. This trait is valuable in many technical and analytical roles.",
            "medium": "You can pay attention to details when needed while maintaining a broader perspective.",
            "low": "You may focus more on the big picture than on details. Consider developing attention to detail for certain roles."
        },
        "creative": {
            "high": "You have a strong creative streak and enjoy artistic or innovative tasks. This trait is valuable in design and creative fields.",
            "medium": "You have some creative abilities while also valuing practical approaches.",
            "low": "You may prefer logical over creative tasks. Consider exploring creative activities if interested in design fields."
        },
        "outgoing": {
            "high": "You're comfortable in social situations and enjoy interacting with others. This trait is valuable in client-facing roles.",
            "medium": "You can be outgoing in certain situations while also valuing quiet time.",
            "low": "You may prefer quieter, less social environments. Consider developing communication skills for people-oriented roles."
        }
    }

    # Generate insights
    insights = []

    for trait, score in trait_scores.items():
        if trait in trait_descriptions:
            if score >= 0.7:
                level = "high"
            elif score >= 0.4:
                level = "medium"
            else:
                level = "low"

            insights.append({
                "trait": trait,
                "score": round(score * 100),
                "level": level,
                "description": trait_descriptions[trait][level]
            })

    # Sort insights by score
    insights = sorted(insights, key=lambda x: x["score"], reverse=True)

    # Limit insights based on plan type
    if plan_type == "free":
        # Free plan gets limited insights (top 3)
        insights = insights[:3]

    return insights