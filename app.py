# app.py

import os
import streamlit as st
import pandas as pd
from rag_engine import (
    get_groq_client,
    load_embedding_model,
    get_chroma_client,
    extract_pdf_pages,
    chunk_pdf_pages,
    index_resume_chunks,
    query_resume_context,
    get_resume_summary,
    perform_jd_gap_analysis,
    answer_resume_question,
    optimize_resume_bullet,
    parse_resume_to_json
)
from templates import get_classic_template, get_modern_sidebar_template

# Page configuration
st.set_page_config(
    page_title="ResuMind - Advanced RAG Resume Builder",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling injection for a premium dark mode UI
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Main font override */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

/* Glassmorphic cards */
.glass-card {
    background: rgba(17, 24, 39, 0.7);
    border-radius: 12px;
    border: 1px solid rgba(59, 130, 246, 0.15);
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
}

.score-badge {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    color: white;
    padding: 10px 20px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 24px;
    display: inline-block;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
}

.metric-card {
    background: rgba(31, 41, 55, 0.5);
    border-left: 4px solid #3b82f6;
    padding: 15px;
    border-radius: 0 8px 8px 0;
    margin-bottom: 12px;
}

/* Tab customizations */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    height: 48px;
    white-space: pre-wrap;
    background-color: rgba(31, 41, 55, 0.4);
    border-radius: 8px 8px 0 0;
    color: #9ca3af;
    padding-left: 20px;
    padding-right: 20px;
    font-weight: 500;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(to right, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2)) !important;
    border-color: rgba(59, 130, 246, 0.5) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "embedding_model" not in st.session_state:
    with st.spinner("Initializing AI Embedding Engine..."):
        st.session_state.embedding_model = load_embedding_model()
        st.session_state.db_client = get_chroma_client()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_pages" not in st.session_state:
    st.session_state.pdf_pages = None
if "chunks" not in st.session_state:
    st.session_state.chunks = None
if "summary_report" not in st.session_state:
    st.session_state.summary_report = None
if "jd_match_report" not in st.session_state:
    st.session_state.jd_match_report = None
if "chroma_collection" not in st.session_state:
    st.session_state.chroma_collection = None
if "current_file_name" not in st.session_state:
    st.session_state.current_file_name = ""
if "resume_json" not in st.session_state:
    st.session_state.resume_json = None
if "last_optimized_bullet" not in st.session_state:
    st.session_state.last_optimized_bullet = ""

# Sidebar Configuration
st.sidebar.markdown("<h2 style='text-align: center; color: #3b82f6;'>📄 ResuMind RAG</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; font-size: 14px; color: #9ca3af;'>Semantic Resume Analysis Engine</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# API Configuration
st.sidebar.subheader("⚙️ API Configuration")
custom_key = st.sidebar.text_input("Groq API Key", type="password", help="Enter your Groq API Key. Get one free at console.groq.com")
llm_model = st.sidebar.selectbox("LLM Model Select", [
    "llama-3.3-70b-versatile",
    "mixtral-8x7b-32768"
], index=0)

# Resolve API Key: sidebar input first, then Streamlit Secrets
api_key = custom_key.strip() if custom_key else st.secrets.get("GROQ_API_KEY", "")

# Block app if no key is provided
if not api_key:
    st.sidebar.warning("🔑 Groq API Key required.")
    st.markdown("""
    <div style='text-align: center; margin-top: 80px;'>
        <h1 style='font-size: 40px; font-weight: 700; background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            Welcome to ResuMind RAG 📄
        </h1>
        <p style='font-size: 17px; color: #9ca3af; max-width: 550px; margin: 20px auto;'>
            Please enter your <b>Groq API Key</b> in the sidebar to get started.<br><br>
            🔑 Get a free key at <a href='https://console.groq.com' target='_blank' style='color: #3b82f6;'>console.groq.com</a>
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

st.sidebar.markdown("---")

# File Upload
st.sidebar.subheader("📤 Document Upload")
uploaded_file = st.sidebar.file_uploader("Upload candidate resume (PDF)", type="pdf")

# Reset states if a different file is uploaded
if uploaded_file is not None and uploaded_file.name != st.session_state.current_file_name:
    st.session_state.current_file_name = uploaded_file.name
    st.session_state.pdf_pages = None
    st.session_state.chunks = None
    st.session_state.summary_report = None
    st.session_state.jd_match_report = None
    st.session_state.chroma_collection = None
    st.session_state.resume_json = None
    st.session_state.messages = []
    st.session_state.last_optimized_bullet = ""

# Main layout logic
if uploaded_file is None:
    # Welcome display when no resume is uploaded
    st.markdown("""
    <div style='text-align: center; margin-top: 50px;'>
        <h1 style='font-size: 50px; font-weight: 700; background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            Supercharge Resume Screening with RAG
        </h1>
        <p style='font-size: 18px; color: #9ca3af; max-width: 650px; margin: 20px auto;'>
            Upload a candidate's resume PDF in the sidebar to review overall scores, 
            run automated gap analysis against job descriptions, and edit/export your resume dynamically.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='glass-card' style='text-align: center;'>
            <h3 style='color: #3b82f6;'>🔍 ATS Scorecard</h3>
            <p style='color: #9ca3af; font-size: 14px;'>Automatically rate professional statements, quantifiable metrics, and formatting alignment.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='glass-card' style='text-align: center;'>
            <h3 style='color: #8b5cf6;'>🎯 Job Description Match</h3>
            <p style='color: #9ca3af; font-size: 14px;'>Perform a RAG-based semantic analysis comparing resume points to JD skills to find critical gaps.</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='glass-card' style='text-align: center;'>
            <h3 style='color: #10b981;'>⚡ STAR Optimizer</h3>
            <p style='color: #9ca3af; font-size: 14px;'>Optimize weak bullet points and directly apply them to your structured templates.</p>
        </div>
        """, unsafe_allow_html=True)

else:
    # Initialize Groq client
    groq_client = get_groq_client(api_key)

    # Extraction and DB pipeline
    if st.session_state.pdf_pages is None:
        with st.spinner("Extracting text from resume pages..."):
            st.session_state.pdf_pages = extract_pdf_pages(uploaded_file)
            st.session_state.chunks = chunk_pdf_pages(st.session_state.pdf_pages)
            
        with st.spinner("Building semantic search vectors (ChromaDB)..."):
            st.session_state.chroma_collection = index_resume_chunks(
                st.session_state.db_client,
                st.session_state.chunks,
                st.session_state.embedding_model
            )
            
        with st.spinner("Deconstructing resume into structured JSON template..."):
            raw_text_full = "\n\n".join([page["text"] for page in st.session_state.pdf_pages])
            try:
                st.session_state.resume_json = parse_resume_to_json(groq_client, raw_text_full, model=llm_model)
            except Exception as e:
                st.error(f"Error parsing resume structure: {e}")

    # Success statistics in sidebar
    st.sidebar.success(f"File: `{uploaded_file.name}`")
    st.sidebar.markdown(f"**Pages Extracted:** {len(st.session_state.pdf_pages)}")
    st.sidebar.markdown(f"**Indexed Chunks:** {len(st.session_state.chunks)}")
    
    # Generate overall summary once
    if st.session_state.summary_report is None:
        with st.spinner("Performing deep candidate screening..."):
            raw_text_full = "\n\n".join([page["text"] for page in st.session_state.pdf_pages])
            try:
                st.session_state.summary_report = get_resume_summary(groq_client, raw_text_full, model=llm_model)
            except Exception as e:
                st.error(f"Error communicating with Groq: {e}")
                st.session_state.summary_report = "Unable to fetch analysis. Check API Key configuration."

    # Render Tabs
    tab_summary, tab_builder, tab_jd, tab_chat, tab_star, tab_raw = st.tabs([
        "👤 Summary & Scorecard",
        "✏️ Resume Builder & PDF Export",
        "🎯 ATS JD Matcher",
        "💬 Interactive Q&A",
        "⚡ STAR Optimizer",
        "🔍 View Extracted Text"
    ])
    
    # TAB 1: Summary & Scorecard
    with tab_summary:
        st.markdown("<h2 style='margin-bottom: 20px;'>Resume Review Dashboard</h2>", unsafe_allow_html=True)
        st.markdown(st.session_state.summary_report)

    # TAB 2: Resume Builder & PDF Export
    with tab_builder:
        st.markdown("<h2>✏️ Structured Resume Builder</h2>", unsafe_allow_html=True)
        st.write("Edit your details below and download a professionally formatted resume instantly.")
        
        if st.session_state.resume_json:
            # Create form containers for editing
            with st.expander("👤 Contact & Personal Info", expanded=True):
                pi = st.session_state.resume_json.get("personal_info", {})
                col1, col2 = st.columns(2)
                with col1:
                    pi["name"] = st.text_input("Full Name", value=pi.get("name", ""))
                    pi["title"] = st.text_input("Professional Title", value=pi.get("title", ""))
                    pi["email"] = st.text_input("Email", value=pi.get("email", ""))
                    pi["phone"] = st.text_input("Phone", value=pi.get("phone", ""))
                with col2:
                    pi["location"] = st.text_input("Location (City, State)", value=pi.get("location", ""))
                    pi["linkedin"] = st.text_input("LinkedIn URL", value=pi.get("linkedin", ""))
                    pi["portfolio"] = st.text_input("Portfolio / GitHub URL", value=pi.get("portfolio", ""))
                st.session_state.resume_json["personal_info"] = pi
            
            with st.expander("📝 Professional Summary", expanded=False):
                st.session_state.resume_json["summary"] = st.text_area(
                    "Profile Summary", 
                    value=st.session_state.resume_json.get("summary", ""), 
                    height=120
                )
                
            with st.expander("🛠 Skills & Languages Inventory", expanded=False):
                skills = st.session_state.resume_json.get("skills", {"technical": [], "concepts": [], "soft": []})
                
                # Format current list of dicts (name & rating) into text for easy editing
                tech_lines = []
                for s in skills.get("technical", []):
                    if isinstance(s, dict):
                        tech_lines.append(f"{s.get('name', '')}: {s.get('rating', 3)}")
                    else:
                        tech_lines.append(f"{s}: 3")
                
                tech_str = st.text_area(
                    "Technical Skills & Proficiency (Format: SkillName: Rating (1-5), one per line)", 
                    value="\n".join(tech_lines),
                    height=150
                )
                
                # Parse technical skills back
                new_tech = []
                for line in tech_str.split("\n"):
                    if ":" in line:
                        parts = line.split(":")
                        name = parts[0].strip()
                        try:
                            rating = int(parts[1].strip())
                        except:
                            rating = 3
                        if name:
                            new_tech.append({"name": name, "rating": rating})
                    elif line.strip():
                        new_tech.append({"name": line.strip(), "rating": 3})
                skills["technical"] = new_tech
                
                # Concepts (AI/ML Concepts)
                concepts_str = st.text_area("AI / ML Concepts (Comma separated)", value=", ".join(skills.get("concepts", [])))
                skills["concepts"] = [s.strip() for s in concepts_str.split(",") if s.strip()]
                
                # Soft Skills
                soft_str = st.text_area("Soft Skills (Comma separated)", value=", ".join(skills.get("soft", [])))
                skills["soft"] = [s.strip() for s in soft_str.split(",") if s.strip()]
                st.session_state.resume_json["skills"] = skills
                
                # Languages
                langs_str = st.text_input("Languages (Comma separated)", value=", ".join(st.session_state.resume_json.get("languages", [])))
                st.session_state.resume_json["languages"] = [l.strip() for l in langs_str.split(",") if l.strip()]
                
            with st.expander("🎓 Education Background", expanded=False):
                for i, edu in enumerate(st.session_state.resume_json.get("education", [])):
                    st.markdown(f"#### Degree {i+1}")
                    col1, col2 = st.columns(2)
                    with col1:
                        edu["degree"] = st.text_input(f"Degree/GPA ({i+1})", value=edu.get("degree", ""), key=f"edu_deg_{i}")
                        edu["institution"] = st.text_input(f"School/University ({i+1})", value=edu.get("institution", ""), key=f"edu_inst_{i}")
                    with col2:
                        edu["year"] = st.text_input(f"Graduation/Duration ({i+1})", value=edu.get("year", ""), key=f"edu_yr_{i}")
                        edu["location"] = st.text_input(f"Location ({i+1})", value=edu.get("location", ""), key=f"edu_loc_{i}")
                    
                    bullets_str = st.text_area(
                        f"Details/Highlights (One per line) ({i+1})",
                        value="\n".join(edu.get("bullets", [])),
                        key=f"edu_bullets_{i}",
                        height=80
                    )
                    edu["bullets"] = [b.strip() for b in bullets_str.split("\n") if b.strip()]
                    
                    if st.button(f"🗑 Remove Degree {i+1}", key=f"rm_edu_{i}"):
                        st.session_state.resume_json["education"].pop(i)
                        st.rerun()
                    st.markdown("---")
                    
                if st.button("➕ Add Education"):
                    st.session_state.resume_json["education"].append({
                        "degree": "", "institution": "", "year": "", "location": "", "bullets": []
                    })
                    st.rerun()

            with st.expander("📈 Work Experience & Leadership", expanded=False):
                # Work experience editor
                for i, job in enumerate(st.session_state.resume_json.get("experience", [])):
                    st.markdown(f"#### Position {i+1}")
                    col1, col2 = st.columns(2)
                    with col1:
                        job["company"] = st.text_input(f"Company/Event/Symposium ({i+1})", value=job.get("company", ""), key=f"job_comp_{i}")
                        job["role"] = st.text_input(f"Role/Title ({i+1})", value=job.get("role", ""), key=f"job_role_{i}")
                    with col2:
                        job["start_date"] = st.text_input(f"Start Date ({i+1})", value=job.get("start_date", ""), key=f"job_sd_{i}")
                        job["end_date"] = st.text_input(f"End Date ({i+1})", value=job.get("end_date", ""), key=f"job_ed_{i}")
                    
                    bullets_str = st.text_area(
                        f"Bullets (One accomplishment per line) ({i+1})", 
                        value="\n".join(job.get("bullets", [])), 
                        key=f"job_bullets_{i}",
                        height=100
                    )
                    job["bullets"] = [b.strip() for b in bullets_str.split("\n") if b.strip()]
                    
                    if st.button(f"🗑 Remove Position {i+1}", key=f"rm_job_{i}"):
                        st.session_state.resume_json["experience"].pop(i)
                        st.rerun()
                    st.markdown("---")
                    
                if st.button("➕ Add Position"):
                    st.session_state.resume_json["experience"].append({
                        "company": "", "role": "", "start_date": "", "end_date": "", "bullets": [""]
                    })
                    st.rerun()
                    
            with st.expander("💻 Academic & Personal Projects", expanded=False):
                for i, proj in enumerate(st.session_state.resume_json.get("projects", [])):
                    st.markdown(f"#### Project {i+1}")
                    col1, col2 = st.columns(2)
                    with col1:
                        proj["name"] = st.text_input(f"Project Name ({i+1})", value=proj.get("name", ""), key=f"proj_name_{i}")
                        proj["technologies"] = st.text_input(f"Technologies/Stack ({i+1})", value=proj.get("technologies", ""), key=f"proj_tech_{i}")
                    with col2:
                        proj["link"] = st.text_input(f"Project Link ({i+1})", value=proj.get("link", ""), key=f"proj_link_{i}")
                    
                    bullets_str = st.text_area(
                        f"Project Bullets (One per line) ({i+1})", 
                        value="\n".join(proj.get("bullets", [])), 
                        key=f"proj_bullets_{i}",
                        height=80
                    )
                    proj["bullets"] = [b.strip() for b in bullets_str.split("\n") if b.strip()]
                    
                    if st.button(f"🗑 Remove Project {i+1}", key=f"rm_proj_{i}"):
                        st.session_state.resume_json["projects"].pop(i)
                        st.rerun()
                    st.markdown("---")
                    
                if st.button("➕ Add Project"):
                    st.session_state.resume_json["projects"].append({
                        "name": "", "technologies": "", "link": "", "bullets": [""]
                    })
                    st.rerun()

            with st.expander("🏆 Hackathons & Competitions", expanded=False):
                if "hackathons" not in st.session_state.resume_json:
                    st.session_state.resume_json["hackathons"] = []
                    
                for i, hack in enumerate(st.session_state.resume_json.get("hackathons", [])):
                    st.markdown(f"#### Hackathon {i+1}")
                    col1, col2 = st.columns(2)
                    with col1:
                        hack["name"] = st.text_input(f"Event Name ({i+1})", value=hack.get("name", ""), key=f"hack_name_{i}")
                    with col2:
                        hack["category"] = st.text_input(f"Details/Category ({i+1})", value=hack.get("category", ""), key=f"hack_cat_{i}")
                    
                    bullets_str = st.text_area(
                        f"Hackathon Bullets (One per line) ({i+1})", 
                        value="\n".join(hack.get("bullets", [])), 
                        key=f"hack_bullets_{i}",
                        height=80
                    )
                    hack["bullets"] = [b.strip() for b in bullets_str.split("\n") if b.strip()]
                    
                    if st.button(f"🗑 Remove Hackathon {i+1}", key=f"rm_hack_{i}"):
                        st.session_state.resume_json["hackathons"].pop(i)
                        st.rerun()
                    st.markdown("---")
                    
                if st.button("➕ Add Hackathon"):
                    st.session_state.resume_json["hackathons"].append({
                        "name": "", "category": "", "bullets": [""]
                    })
                    st.rerun()

            # --- Live Preview & Export Container ---
            st.markdown("<h3 style='margin-top: 30px;'>🖥️ Resume Live Preview & Export</h3>", unsafe_allow_html=True)
            template_choice = st.selectbox("Select Resume Layout Style", ["Classic Minimalist", "Modern Sidebar"])
            
            if template_choice == "Classic Minimalist":
                html_resume = get_classic_template(st.session_state.resume_json)
            else:
                html_resume = get_modern_sidebar_template(st.session_state.resume_json)
                
            # Render the preview in an iframe
            st.components.v1.html(html_resume, height=800, scrolling=True)
            
            # Download HTML Button
            st.download_button(
                label="💾 Download HTML Resume",
                data=html_resume,
                file_name=f"{st.session_state.resume_json['personal_info'].get('name', 'Resume').replace(' ', '_')}_Resume.html",
                mime="text/html",
                type="primary"
            )
            st.info("💡 **Tip to Save as PDF:** Open the downloaded HTML file in your web browser (Chrome, Edge, Safari), press **Ctrl + P** (or Cmd + P), set your destination to **'Save as PDF'**, and ensure **'Background graphics'** is checked for the best styling rendering!")
            
        else:
            st.warning("No structured resume data found. Make sure you uploaded a PDF resume first!")

    # TAB 3: ATS Job Description Matcher
    with tab_jd:
        st.markdown("<h2>Target JD Alignment (RAG semantic gap analysis)</h2>", unsafe_allow_html=True)
        st.write("Paste the job posting description below to check the candidate's technical alignment.")
        
        jd_input = st.text_area("Job Description Details", height=200, placeholder="Paste the target job description here...")
        
        if st.button("Analyze Job Fit", type="primary"):
            if jd_input.strip() == "":
                st.warning("Please provide a valid Job Description.")
            else:
                with st.spinner("Querying resume vectors & evaluating skills alignment..."):
                    # Use JD as query to retrieve most relevant chunks of the resume
                    retrieved_context, _ = query_resume_context(
                        st.session_state.chroma_collection,
                        jd_input,
                        st.session_state.embedding_model,
                        n_results=6
                    )
                    
                    try:
                        st.session_state.jd_match_report = perform_jd_gap_analysis(
                            groq_client,
                            jd_input,
                            retrieved_context,
                            model=llm_model
                        )
                    except Exception as e:
                        st.error(f"Groq API error: {e}")
                        st.session_state.jd_match_report = "Error analyzing alignment."
                        
        if st.session_state.jd_match_report:
            st.markdown("---")
            st.markdown(st.session_state.jd_match_report)

    # TAB 4: Interactive Q&A (Conversational RAG)
    with tab_chat:
        st.markdown("<h2>Query Candidate Content & Career Scenarios</h2>", unsafe_allow_html=True)
        st.write("Ask specific resume questions (*'What React projects did they do?'*) or general career advice scenarios.")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        user_query = st.chat_input("Ask a question...")
        
        if user_query:
            # Display user's question
            with st.chat_message("user"):
                st.markdown(user_query)
            st.session_state.messages.append({"role": "user", "content": user_query})
            
            with st.spinner("Searching resume content and generating answer..."):
                # Semantic search ChromaDB
                retrieved_context, _ = query_resume_context(
                    st.session_state.chroma_collection,
                    user_query,
                    st.session_state.embedding_model,
                    n_results=5
                )
            
                try:
                    answer = answer_resume_question(
                        groq_client,
                        user_query,
                        retrieved_context,
                        chat_history=st.session_state.messages,
                        model=llm_model
                    )
                except Exception as e:
                    answer = f"Error generating response: {e}"
            
            with st.chat_message("assistant"):
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    with tab_star:
        st.markdown("<h2>STAR Method Bullet Optimizer</h2>", unsafe_allow_html=True)
        st.write("Rewrite individual bullet points to highlight results, percentages, and leadership impact.")
        
        col_inp, col_out = st.columns([1, 1])
        
        with col_inp:
            st.subheader("Input Bullet Point")
            bullet_input = st.text_area("Original Statement", placeholder="e.g., I was responsible for fixing bugs and updating the website frontend.", height=120)
            role_input = st.text_input("Role / Context (Optional)", placeholder="e.g., Junior Frontend Developer")
            optimize_btn = st.button("Optimize Statement", type="primary")
            
        with col_out:
            st.subheader("High-Impact Suggestion")
            optimized_text = ""
            if optimize_btn:
                if bullet_input.strip() == "":
                    st.warning("Please type a bullet point to rewrite.")
                else:
                    with st.spinner("Generating STAR suggestions..."):
                        try:
                            optimized_text = optimize_resume_bullet(
                                groq_client,
                                bullet_input,
                                role_input,
                                model=llm_model
                            )
                            st.session_state.last_optimized_bullet = optimized_text
                            st.markdown(f"<div class='glass-card'>{optimized_text}</div>", unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Error optimizing bullet point: {e}")
            elif st.session_state.last_optimized_bullet:
                st.markdown(f"<div class='glass-card'>{st.session_state.last_optimized_bullet}</div>", unsafe_allow_html=True)
                optimized_text = st.session_state.last_optimized_bullet
            else:
                st.info("Submit a statement to view the optimized rewrite.")
                
            # Direct Apply Feature
            if st.session_state.resume_json and (optimized_text or st.session_state.last_optimized_bullet):
                current_text = optimized_text if optimized_text else st.session_state.last_optimized_bullet
                st.markdown("---")
                st.subheader("⚡ Apply directly to Resume Builder")
                
                # Extract rewritten bullet point from markdown if possible
                clean_rewrite = ""
                lines = current_text.split('\n')
                for line in lines:
                    if "Rewritten" in line:
                        clean_rewrite = line.split("Recommended):")[-1].replace("**", "").strip()
                        break
                if not clean_rewrite:
                    clean_rewrite = bullet_input
                
                st.write(f"**Cleaned Rewrite to Apply:** *{clean_rewrite}*")
                
                # Choose where to apply
                exp_options = [f"Job {i+1}: {job.get('role')} at {job.get('company')}" for i, job in enumerate(st.session_state.resume_json.get("experience", []))]
                proj_options = [f"Project {i+1}: {proj.get('name')}" for i, proj in enumerate(st.session_state.resume_json.get("projects", []))]
                hack_options = [f"Hackathon {i+1}: {hack.get('name')}" for i, hack in enumerate(st.session_state.resume_json.get("hackathons", []))] if "hackathons" in st.session_state.resume_json else []
                
                target_category = st.radio("Apply to Category:", ["Work Experience", "Projects", "Hackathons"])
                
                if target_category == "Work Experience" and exp_options:
                    selected_job_idx = st.selectbox("Select Job Position", range(len(exp_options)), format_func=lambda x: exp_options[x])
                    bullets_in_job = st.session_state.resume_json["experience"][selected_job_idx].get("bullets", [])
                    
                    bullet_idx_options = [f"Replace Bullet {k+1}: {b[:40]}..." for k, b in enumerate(bullets_in_job)]
                    bullet_idx_options.append("[NEW] Add as a new bullet point at the end")
                    
                    selected_bullet_idx = st.selectbox("Select target bullet point", range(len(bullet_idx_options)), format_func=lambda x: bullet_idx_options[x])
                    
                    if st.button("Apply to Selected Job"):
                        if selected_bullet_idx == len(bullets_in_job):
                            st.session_state.resume_json["experience"][selected_job_idx]["bullets"].append(clean_rewrite)
                        else:
                            st.session_state.resume_json["experience"][selected_job_idx]["bullets"][selected_bullet_idx] = clean_rewrite
                        st.success("Successfully applied! Check your updated resume in the 'Resume Builder' tab.")
                        
                elif target_category == "Projects" and proj_options:
                    selected_proj_idx = st.selectbox("Select Project", range(len(proj_options)), format_func=lambda x: proj_options[x])
                    bullets_in_proj = st.session_state.resume_json["projects"][selected_proj_idx].get("bullets", [])
                    
                    bullet_idx_options = [f"Replace Bullet {k+1}: {b[:40]}..." for k, b in enumerate(bullets_in_proj)]
                    bullet_idx_options.append("[NEW] Add as a new bullet point at the end")
                    
                    selected_bullet_idx = st.selectbox("Select target bullet point", range(len(bullet_idx_options)), format_func=lambda x: bullet_idx_options[x])
                    
                    if st.button("Apply to Selected Project"):
                        if selected_bullet_idx == len(bullets_in_proj):
                            st.session_state.resume_json["projects"][selected_proj_idx]["bullets"].append(clean_rewrite)
                        else:
                            st.session_state.resume_json["projects"][selected_proj_idx]["bullets"][selected_bullet_idx] = clean_rewrite
                        st.success("Successfully applied! Check your updated resume in the 'Resume Builder' tab.")
                        
                elif target_category == "Hackathons" and hack_options:
                    selected_hack_idx = st.selectbox("Select Hackathon", range(len(hack_options)), format_func=lambda x: hack_options[x])
                    bullets_in_hack = st.session_state.resume_json["hackathons"][selected_hack_idx].get("bullets", [])
                    
                    bullet_idx_options = [f"Replace Bullet {k+1}: {b[:40]}..." for k, b in enumerate(bullets_in_hack)]
                    bullet_idx_options.append("[NEW] Add as a new bullet point at the end")
                    
                    selected_bullet_idx = st.selectbox("Select target bullet point", range(len(bullet_idx_options)), format_func=lambda x: bullet_idx_options[x])
                    
                    if st.button("Apply to Selected Hackathon"):
                        if selected_bullet_idx == len(bullets_in_hack):
                            st.session_state.resume_json["hackathons"][selected_hack_idx]["bullets"].append(clean_rewrite)
                        else:
                            st.session_state.resume_json["hackathons"][selected_hack_idx]["bullets"][selected_bullet_idx] = clean_rewrite
                        st.success("Successfully applied! Check your updated resume in the 'Resume Builder' tab.")

    with tab_raw:
        st.markdown("<h2>Page-by-Page Raw Extracted Text</h2>", unsafe_allow_html=True)
        for page in st.session_state.pdf_pages:
            with st.expander(f"📄 Page {page['page_number']}"):
                st.text(page["text"])