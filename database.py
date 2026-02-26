import os
from neo4j import GraphDatabase

# Configure Neo4j connection details
# For local Neo4j desktop, URI is usually "bolt://localhost:7687" or "neo4j://localhost:7687"
# For Neo4j AuraDB (Cloud), use the URI provided in your console (e.g., "neo4j+s://<db_id>.databases.neo4j.io")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password") # Default password, CHANGE THIS in production

class GraphDB:
    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Verify connectivity
            self.driver.verify_connectivity()
            print("Successfully connected to Neo4j database.")
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def add_user(self, user_id, name, current_role=None):
        if not self.driver: return None
        query = (
            "MERGE (u:User {id: $user_id}) "
            "ON CREATE SET u.name = $name, u.current_role = $current_role "
            "ON MATCH SET u.name = $name, u.current_role = $current_role "
            "RETURN u"
        )
        with self.driver.session() as session:
            result = session.run(query, user_id=user_id, name=name, current_role=current_role)
            return result.single()

    def add_skill(self, skill_name, category="Technical"):
        if not self.driver: return None
        # Normalize skill name (lowercase, stripped) for cleaner matching
        skill_name_clean = skill_name.strip().lower()
        query = (
            "MERGE (s:Skill {name: $skill_name}) "
            "ON CREATE SET s.display_name = $original_name, s.category = $category "
            "RETURN s"
        )
        with self.driver.session() as session:
            result = session.run(query, skill_name=skill_name_clean, original_name=skill_name, category=category)
            return result.single()

    def add_job_role(self, title, company=None):
        if not self.driver: return None
        title_clean = title.strip().lower()
        query = (
            "MERGE (j:JobRole {title: $title}) "
            "ON CREATE SET j.display_title = $original_title, j.company = $company "
            "RETURN j"
        )
        with self.driver.session() as session:
            result = session.run(query, title=title_clean, original_title=title, company=company)
            return result.single()

    def user_has_skill(self, user_id, skill_name, proficiency="Intermediate"):
        if not self.driver: return None
        skill_name_clean = skill_name.strip().lower()
        query = (
            "MATCH (u:User {id: $user_id}) "
            "MATCH (s:Skill {name: $skill_name}) "
            "MERGE (u)-[r:HAS_SKILL]->(s) "
            "SET r.proficiency = $proficiency "
            "RETURN r"
        )
        with self.driver.session() as session:
            result = session.run(query, user_id=user_id, skill_name=skill_name_clean, proficiency=proficiency)
            return result.single()

    def job_requires_skill(self, job_title, skill_name, is_core=True):
        if not self.driver: return None
        job_title_clean = job_title.strip().lower()
        skill_name_clean = skill_name.strip().lower()
        query = (
            "MATCH (j:JobRole {title: $job_title}) "
            "MATCH (s:Skill {name: $skill_name}) "
            "MERGE (j)-[r:REQUIRES]->(s) "
            "SET r.is_core = $is_core "
            "RETURN r"
        )
        with self.driver.session() as session:
            result = session.run(query, job_title=job_title_clean, skill_name=skill_name_clean, is_core=is_core)
            return result.single()

# Initialize the global DB instance
db = GraphDB(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

if __name__ == "__main__":
    # Quick test when running this file directly
    if db.driver:
        print("Testing DB inserts...")
        db.add_user("user_123", "Alice Engineer", "Software Developer")
        db.add_skill("Python")
        db.add_skill("Neo4j", category="Database")
        db.add_job_role("Senior Python Developer", "TechCorp")
        
        db.user_has_skill("user_123", "Python", "Advanced")
        db.job_requires_skill("Senior Python Developer", "Python")
        db.job_requires_skill("Senior Python Developer", "Neo4j")
        print("Test complete. Check your Neo4j browser.")
        db.close()
    else:
        print("Skipping tests - No Neo4j connection.")
