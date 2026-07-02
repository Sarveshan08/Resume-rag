# templates.py

def render_dots(rating):
    """
    Renders 5 circular indicator dots based on skill level.
    Filled: ●, Empty: ○
    """
    try:
        r = int(rating)
    except:
        r = 3
    r = max(1, min(5, r))
    return "●" * r + "○" * (5 - r)

def get_classic_template(data):
    """
    Generates a single-column, high-impact, print-ready ATS resume layout (Kathir style).
    """
    pi = data.get("personal_info", {})
    summary = data.get("summary", "")
    skills = data.get("skills", {})
    experience = data.get("experience", [])
    projects = data.get("projects", [])
    hackathons = data.get("hackathons", [])
    education = data.get("education", [])
    languages = data.get("languages", [])
    
    # Format Header
    contact_parts = []
    if pi.get("location"):
        contact_parts.append(pi["location"])
    if pi.get("phone"):
        contact_parts.append(pi["phone"])
    if pi.get("email"):
        contact_parts.append(f'<a href="mailto:{pi["email"]}">{pi["email"]}</a>')
    if pi.get("linkedin"):
        contact_parts.append(f'<a href="https://{pi["linkedin"].replace("https://", "")}" target="_blank">{pi["linkedin"]}</a>')
    if pi.get("portfolio"):
        contact_parts.append(f'<a href="https://{pi["portfolio"].replace("https://", "")}" target="_blank">{pi["portfolio"]}</a>')
        
    contact_html = " | ".join(contact_parts)
    
    # Format Education HTML
    edu_html = ""
    for edu in education:
        bullets = "".join([f"<li>{bullet}</li>" for bullet in edu.get("bullets", [])])
        bullets_html = f"<ul>{bullets}</ul>" if bullets else ""
        edu_html += f"""
        <div class="section-item">
            <div class="item-header">
                <span class="item-title">{edu.get("degree", "")}</span>
                <span class="item-date">{edu.get("year", "")}</span>
            </div>
            <div class="item-subtitle">{edu.get("institution", "")}{f', {edu.get("location", "")}' if edu.get("location") else ''}</div>
            {bullets_html}
        </div>
        """
        
    # Format Technical Skills
    tech_list = skills.get("technical", [])
    tech_html = ""
    # Process in pairs for 2-column layout
    for idx in range(0, len(tech_list), 2):
        item_left = tech_list[idx]
        name_left = item_left.get("name", "") if isinstance(item_left, dict) else item_left
        rating_left = render_dots(item_left.get("rating", 3)) if isinstance(item_left, dict) else "●●●○○"
        
        right_col_html = '<div class="skill-item"></div>'
        if idx + 1 < len(tech_list):
            item_right = tech_list[idx+1]
            name_right = item_right.get("name", "") if isinstance(item_right, dict) else item_right
            rating_right = render_dots(item_right.get("rating", 3)) if isinstance(item_right, dict) else "●●●○○"
            right_col_html = f"""
            <div class="skill-item">
                <span class="skill-name">{name_right}</span>
                <span class="skill-dots">{rating_right}</span>
            </div>
            """
            
        tech_html += f"""
        <div class="skills-row">
            <div class="skill-item">
                <span class="skill-name">{name_left}</span>
                <span class="skill-dots">{rating_left}</span>
            </div>
            {right_col_html}
        </div>
        """
        
    # Format AI / ML Concepts & Soft Skills
    concepts_html = " | ".join(skills.get("concepts", []))
    soft_html = " | ".join(skills.get("soft", []))
    
    # Format Skills block
    skills_html = ""
    if tech_html or concepts_html or soft_html:
        skills_html += '<div class="section"><div class="section-title">Skills</div>'
        if tech_html:
            skills_html += f'<div class="skills-subheader">Technical Skills</div><div class="skills-table">{tech_html}</div>'
        if concepts_html:
            skills_html += f'<div class="skills-subheader" style="margin-top: 8px;">AI / ML Concepts</div><div style="font-size: 13px;">{concepts_html}</div>'
        if soft_html:
            skills_html += f'<div class="skills-subheader" style="margin-top: 8px;">Soft Skills</div><div style="font-size: 13px;">{soft_html}</div>'
        skills_html += '</div>'
        
    # Format Projects HTML
    proj_html = ""
    for proj in projects:
        bullets = "".join([f"<li>{bullet}</li>" for bullet in proj.get("bullets", [])])
        proj_html += f"""
        <div class="section-item">
            <div class="item-header">
                <span class="item-title">{proj.get("name", "")}</span>
                <span class="item-tech">{proj.get("technologies", "")}</span>
            </div>
            <ul>{bullets}</ul>
        </div>
        """
        
    # Format Experience HTML
    exp_html = ""
    for exp in experience:
        bullets = "".join([f"<li>{bullet}</li>" for bullet in exp.get("bullets", [])])
        exp_html += f"""
        <div class="section-item">
            <div class="item-header">
                <span class="item-title">{exp.get("role", "")}</span>
                <span class="item-tech">{exp.get("company", "")}</span>
            </div>
            <ul>{bullets}</ul>
        </div>
        """
        
    # Format Hackathons HTML
    hack_html = ""
    for hack in hackathons:
        bullets = "".join([f"<li>{bullet}</li>" for bullet in hack.get("bullets", [])])
        hack_html += f"""
        <div class="section-item">
            <div class="item-header">
                <span class="item-title">{hack.get("name", "")}</span>
                <span class="item-tech">{hack.get("category", "")}</span>
            </div>
            <ul>{bullets}</ul>
        </div>
        """
        
    # Format Languages HTML
    lang_html = ""
    if languages:
        lang_html = f"""
        <div class="section" style="margin-bottom: 10px;">
            <div class="section-title">Languages</div>
            <div style="font-size: 13px;">{" | ".join(languages)}</div>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{pi.get("name", "Resume")}</title>
        <style>
            body {{
                font-family: 'Arial', 'Helvetica Neue', Helvetica, sans-serif;
                color: #000;
                line-height: 1.35;
                margin: 0;
                padding: 30px 40px;
                background-color: #fff;
            }}
            .header {{
                text-align: center;
                margin-bottom: 15px;
            }}
            .name {{
                font-size: 26px;
                font-weight: bold;
                letter-spacing: 0.5px;
                margin: 0 0 2px 0;
                text-transform: uppercase;
            }}
            .title {{
                font-size: 13px;
                font-style: italic;
                color: #333;
                margin: 0 0 5px 0;
            }}
            .contact-info {{
                font-size: 11px;
                color: #000;
            }}
            .contact-info a {{
                color: #000;
                text-decoration: none;
            }}
            .header-line {{
                border-bottom: 2px solid #000;
                margin-top: 10px;
                margin-bottom: 15px;
            }}
            .section {{
                margin-bottom: 18px;
            }}
            .section-title {{
                font-size: 13px;
                font-weight: bold;
                text-transform: uppercase;
                border-bottom: 1px solid #000;
                padding-bottom: 2px;
                margin-top: 14px;
                margin-bottom: 8px;
                letter-spacing: 0.5px;
            }}
            .section-item {{
                margin-bottom: 10px;
                page-break-inside: avoid;
            }}
            .item-header {{
                display: flex;
                justify-content: space-between;
                font-size: 13px;
            }}
            .item-title {{
                font-weight: bold;
            }}
            .item-subtitle {{
                font-size: 13px;
                font-style: italic;
                margin-top: 1px;
                margin-bottom: 3px;
            }}
            .item-date {{
                font-weight: normal;
            }}
            .item-tech {{
                font-style: italic;
                color: #333;
            }}
            ul {{
                margin: 3px 0 6px 15px;
                padding: 0;
                list-style-type: none;
            }}
            li {{
                font-size: 13px;
                position: relative;
                margin-bottom: 2px;
            }}
            li::before {{
                content: "– ";
                position: absolute;
                left: -15px;
            }}
            
            /* Skills Table Styling */
            .skills-subheader {{
                font-size: 12px;
                font-weight: bold;
                text-decoration: underline;
                margin-bottom: 4px;
            }}
            .skills-table {{
                width: 100%;
                margin-bottom: 4px;
            }}
            .skills-row {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 2px;
            }}
            .skill-item {{
                width: 47%;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 13px;
            }}
            .skill-name {{
                font-weight: normal;
            }}
            .skill-dots {{
                font-family: monospace;
                letter-spacing: 2px;
                font-size: 11px;
            }}
            
            @media print {{
                body {{
                    padding: 0;
                }}
                @page {{
                    size: letter;
                    margin: 0.4in;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="name">{pi.get("name", "")}</div>
            {f'<div class="title">{pi.get("title", "")}</div>' if pi.get("title") else ""}
            <div class="contact-info">{contact_html}</div>
        </div>
        <div class="header-line"></div>
        
        {f'<div class="section"><div class="section-title">Professional Summary</div><p style="font-size: 13px; margin: 0; text-align: justify;">{summary}</p></div>' if summary else ""}
        
        {f'<div class="section"><div class="section-title">Education</div>{edu_html}</div>' if edu_html else ""}
        
        {skills_html}
        
        {f'<div class="section"><div class="section-title">Projects</div>{proj_html}</div>' if proj_html else ""}
        
        {f'<div class="section"><div class="section-title">Experience & Leadership</div>{exp_html}</div>' if exp_html else ""}
        
        {f'<div class="section"><div class="section-title">Hackathons</div>{hack_html}</div>' if hack_html else ""}
        
        {lang_html}
    </body>
    </html>
    """
    return html_content


def get_modern_sidebar_template(data):
    """
    Keep the two-column sidebar layout as a template option.
    """
    # (Leaving this intact as it was defined, but we'll use render_dots helper for ratings if available)
    pi = data.get("personal_info", {})
    summary = data.get("summary", "")
    skills = data.get("skills", {})
    experience = data.get("experience", [])
    projects = data.get("projects", [])
    education = data.get("education", [])
    
    exp_html = ""
    for exp in experience:
        bullets = "".join([f"<li>{bullet}</li>" for bullet in exp.get("bullets", [])])
        exp_html += f"""
        <div class="section-item">
            <div class="item-header">
                <span class="item-title">{exp.get("role", "")}</span>
                <span class="item-date">{exp.get("start_date", "")} - {exp.get("end_date", "")}</span>
            </div>
            <div class="item-sub">{exp.get("company", "")}</div>
            <ul>{bullets}</ul>
        </div>
        """
        
    proj_html = ""
    for proj in projects:
        bullets = "".join([f"<li>{bullet}</li>" for bullet in proj.get("bullets", [])])
        link_html = f'<a href="{proj.get("link", "")}" class="item-link" target="_blank">Live Link</a>' if proj.get("link") else ""
        proj_html += f"""
        <div class="section-item">
            <div class="item-header">
                <span class="item-title">{proj.get("name", "")}</span>
                {link_html}
            </div>
            <div class="item-sub" style="font-size: 11px; font-weight: normal; color: #555;">Technologies: {proj.get("technologies", "")}</div>
            <ul>{bullets}</ul>
        </div>
        """
        
    tech_skills_html = ""
    for s in skills.get("technical", []):
        name = s.get("name", s) if isinstance(s, dict) else s
        tech_skills_html += f'<span class="badge">{name}</span>'
        
    soft_skills_html = "".join([f'<span class="badge badge-soft">{s}</span>' for s in skills.get("soft", [])])
    
    edu_html = ""
    for edu in education:
        edu_html += f"""
        <div class="edu-item">
            <div class="edu-degree">{edu.get("degree", "")}</div>
            <div class="edu-school">{edu.get("institution", "")}</div>
            <div class="edu-date">{edu.get("year", "")} | {edu.get("location", "")}</div>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{pi.get("name", "Resume")}</title>
        <style>
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                color: #334155;
                margin: 0;
                padding: 0;
                background-color: #fff;
                display: flex;
                min-height: 100vh;
            }}
            .sidebar {{
                width: 32%;
                background-color: #0f172a;
                color: #e2e8f0;
                padding: 35px 25px;
                box-sizing: border-box;
            }}
            .main-content {{
                width: 68%;
                padding: 40px 35px;
                box-sizing: border-box;
            }}
            .name {{
                font-size: 28px;
                font-weight: 700;
                color: #0f172a;
                margin: 0 0 5px 0;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .title {{
                font-size: 15px;
                color: #4f46e5;
                font-weight: 600;
                margin: 0 0 20px 0;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .contact-block {{
                margin-top: 30px;
                font-size: 13px;
            }}
            .contact-title {{
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #94a3b8;
                border-bottom: 1px solid #334155;
                padding-bottom: 5px;
                margin-bottom: 15px;
            }}
            .contact-item {{
                margin-bottom: 12px;
                word-wrap: break-word;
            }}
            .contact-item a {{
                color: #cbd5e1;
                text-decoration: none;
            }}
            .sidebar-section {{
                margin-top: 35px;
            }}
            .sidebar-title {{
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #94a3b8;
                border-bottom: 1px solid #334155;
                padding-bottom: 5px;
                margin-bottom: 15px;
            }}
            .badge-container {{
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
            }}
            .badge {{
                background-color: #1e293b;
                color: #38bdf8;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 8px;
                border-radius: 4px;
                border: 1px solid #334155;
            }}
            .badge-soft {{
                color: #a78bfa;
            }}
            .edu-item {{
                margin-bottom: 15px;
            }}
            .edu-degree {{
                font-size: 13px;
                font-weight: 600;
                color: #f8fafc;
            }}
            .edu-school {{
                font-size: 12px;
                color: #cbd5e1;
            }}
            .edu-date {{
                font-size: 11px;
                color: #94a3b8;
                font-style: italic;
            }}
            .section {{
                margin-bottom: 30px;
            }}
            .section-title {{
                font-size: 15px;
                font-weight: 700;
                text-transform: uppercase;
                color: #0f172a;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 5px;
                margin-bottom: 15px;
                letter-spacing: 1px;
            }}
            .section-item {{
                margin-bottom: 20px;
                page-break-inside: avoid;
            }}
            .item-header {{
                display: flex;
                justify-content: space-between;
                font-size: 14px;
                font-weight: 600;
                color: #0f172a;
            }}
            .item-sub {{
                font-size: 13px;
                color: #4f46e5;
                font-weight: 500;
                margin: 2px 0 6px 0;
            }}
            .item-date {{
                font-weight: normal;
                font-size: 12px;
                color: #64748b;
            }}
            .item-link {{
                font-size: 12px;
                color: #4f46e5;
                text-decoration: none;
            }}
            ul {{
                margin: 0 0 0 15px;
                padding: 0;
                font-size: 13px;
                color: #334155;
            }}
            li {{
                margin-bottom: 4px;
            }}
            @media print {{
                body {{
                    flex-direction: row;
                    min-height: 0;
                }}
                .sidebar {{
                    width: 32% !important;
                    background-color: #0f172a !important;
                    -webkit-print-color-adjust: exact;
                    print-color-adjust: exact;
                }}
                .main-content {{
                    width: 68% !important;
                }}
                @page {{
                    size: letter;
                    margin: 0;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div style="text-align: center; margin-bottom: 15px;">
                <div style="font-size: 50px; line-height: 1;">👤</div>
            </div>
            
            <div class="contact-block">
                <div class="contact-title">Contact</div>
                <div class="contact-item">📍 {pi.get("location", "")}</div>
                <div class="contact-item">📞 {pi.get("phone", "")}</div>
                <div class="contact-item">✉️ <a href="mailto:{pi.get("email", "")}">{pi.get("email", "")}</a></div>
                {f'<div class="contact-item">🔗 <a href="{pi.get("linkedin", "")}" target="_blank">LinkedIn</a></div>' if pi.get("linkedin") else ""}
                {f'<div class="contact-item">💻 <a href="{pi.get("portfolio", "")}" target="_blank">Portfolio</a></div>' if pi.get("portfolio") else ""}
            </div>
            
            {f'<div class="sidebar-section"><div class="sidebar-title">Tech Skills</div><div class="badge-container">{tech_skills_html}</div></div>' if tech_skills_html else ""}
            
            {f'<div class="sidebar-section"><div class="sidebar-title">Soft Skills</div><div class="badge-container">{soft_skills_html}</div></div>' if soft_skills_html else ""}
            
            {f'<div class="sidebar-section"><div class="sidebar-title">Education</div>{edu_html}</div>' if edu_html else ""}
        </div>
        
        <div class="main-content">
            <div class="name">{pi.get("name", "")}</div>
            <div class="title">{pi.get("title", "")}</div>
            
            {f'<div class="section"><div class="section-title">Profile</div><p style="font-size: 13px; margin: 0; text-align: justify;">{summary}</p></div>' if summary else ""}
            
            {f'<div class="section"><div class="section-title">Experience</div>{exp_html}</div>' if exp_html else ""}
            
            {f'<div class="section"><div class="section-title">Projects</div>{proj_html}</div>' if proj_html else ""}
        </div>
    </body>
    </html>
    """
    return html_content