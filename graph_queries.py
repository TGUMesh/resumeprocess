from database import db

def analyze_skill_gap(user_id, target_job_title):
    """
    Given a User and a Target Job Role, find the core skills the user is missing.
    Returns a list of missing skill nodes.
    """
    if not db.driver:
        return []

    job_title_clean = target_job_title.strip().lower()
    
    # Cypher Query Logic:
    # 1. Match the specific user
    # 2. Match the specific target job
    # 3. Find all skills that the job REQUIREs
    # 4. Filter out any skills the user already HAS_SKILL for
    query = """
    MATCH (u:User {id: $user_id})
    MATCH (j:JobRole {title: $job_title})
    MATCH (j)-[r:REQUIRES]->(required_skill:Skill)
    WHERE r.is_core = true 
      AND NOT (u)-[:HAS_SKILL]->(required_skill)
    RETURN required_skill.name AS missing_skill, required_skill.category AS category
    """
    
    missing_skills = []
    with db.driver.session() as session:
        result = session.run(query, user_id=user_id, job_title=job_title_clean)
        for record in result:
            missing_skills.append({
                "skill": record["missing_skill"],
                "category": record["category"]
            })
            
    return missing_skills

def get_user_graph_data(user_id, target_job_title=None):
    """
    Retrieves the necessary nodes and edges to visualize the user's graph in D3.js.
    """
    if not db.driver:
        return {"nodes": [], "links": []}

    nodes = []
    links = []
    
    # Get User Data
    user_query = "MATCH (u:User {id: $user_id}) RETURN u.id AS id, u.name AS name"
    with db.driver.session() as session:
        user_res = session.run(user_query, user_id=user_id).single()
        if user_res:
            nodes.append({"id": user_res["name"], "group": 1, "type": "user"})
            
    # Get User's Current Skills
    skills_query = """
    MATCH (u:User {id: $user_id})-[r:HAS_SKILL]->(s:Skill)
    RETURN s.name AS skill, r.proficiency AS proficiency, u.name as user_name
    """
    with db.driver.session() as session:
        skills_res = session.run(skills_query, user_id=user_id)
        for record in skills_res:
            nodes.append({"id": record["skill"], "group": 2, "type": "skill_owned"})
            links.append({"source": record["user_name"], "target": record["skill"], "value": 1, "label": "HAS_SKILL"})

    # If a target job is specified, add it and its required skills (highlighting missing ones)
    if target_job_title:
        job_title_clean = target_job_title.strip().lower()
        job_query = """
        MATCH (j:JobRole {title: $job_title})
        RETURN j.display_title AS title
        """
        with db.driver.session() as session:
            job_res = session.run(job_query, job_title=job_title_clean).single()
            if job_res:
                nodes.append({"id": job_res["title"], "group": 3, "type": "job"})
                
                # Get required skills
                req_query = """
                MATCH (j:JobRole {title: $job_title})-[r:REQUIRES]->(s:Skill)
                OPTIONAL MATCH (u:User {id: $user_id})-[has:HAS_SKILL]->(s)
                RETURN s.name AS skill, s.category AS category, has IS NOT NULL AS user_has_it
                """
                req_res = session.run(req_query, job_title=job_title_clean, user_id=user_id)
                for record in req_res:
                    skill_id = record["skill"]
                    # Add node if not already in the list
                    if not any(n["id"] == skill_id for n in nodes):
                        group = 2 if record["user_has_it"] else 4 # 4 represents missing skills (red)
                        node_type = "skill_owned" if record["user_has_it"] else "skill_missing"
                        nodes.append({"id": skill_id, "group": group, "type": node_type})
                    
                    # Link Job to Skill
                    links.append({"source": job_res["title"], "target": skill_id, "value": 1, "label": "REQUIRES"})

    return {"nodes": nodes, "links": links}

if __name__ == "__main__":
    # Test queries
    print("Testing Graph Queries for user_123...")
    gaps = analyze_skill_gap("user_123", "Senior Python Developer")
    print(f"Missing skills: {gaps}")
    
    vis_data = get_user_graph_data("user_123", "Senior Python Developer")
    print(f"Graph Nodes: {len(vis_data['nodes'])}, Links: {len(vis_data['links'])}")
