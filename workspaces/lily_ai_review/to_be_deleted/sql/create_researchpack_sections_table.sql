-- Create the saas_researchpack_sections table if it doesn't exist
CREATE TABLE IF NOT EXISTS saas_researchpack_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    section_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    display_order INT NOT NULL,
    include_diagrams BOOLEAN DEFAULT FALSE,
    diagram_type VARCHAR(255),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Delete existing data to avoid duplicates
DELETE FROM saas_researchpack_sections;

-- Insert default section configuration
INSERT INTO saas_researchpack_sections (section_name, display_name, display_order, include_diagrams, diagram_type, enabled)
VALUES
    ('about_lily', 'About Lily AI', 1, FALSE, NULL, TRUE),
    ('how_to_use', 'How to Use This Pack', 2, FALSE, NULL, TRUE),
    ('introduction', 'Introduction', 3, TRUE, 'question_breakdown', TRUE),
    ('topic_analysis', 'Topic Analysis', 4, TRUE, 'mind_map', TRUE),
    ('methodological_approaches', 'Methodological Approaches', 5, TRUE, 'journey_map', TRUE),
    ('key_arguments', 'Key Arguments', 6, TRUE, 'argument_mapping', TRUE),
    ('citations_resources', 'Citations and Resources', 7, FALSE, NULL, TRUE),
    ('personalized_questions', 'Personalized Questions', 8, FALSE, NULL, TRUE),
    ('appendices', 'Appendices', 9, FALSE, NULL, TRUE);

-- Create a trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
DROP TRIGGER IF EXISTS update_saas_researchpack_sections_updated_at ON saas_researchpack_sections;
CREATE TRIGGER update_saas_researchpack_sections_updated_at
BEFORE UPDATE ON saas_researchpack_sections
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
