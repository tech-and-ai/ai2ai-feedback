-- Delete existing data to avoid duplicates
DELETE FROM saas_researchpack_sections;

-- Insert default section configuration
INSERT INTO saas_researchpack_sections (
    name, 
    display_name, 
    section_order, 
    enabled, 
    required, 
    include_diagrams, 
    diagram_type, 
    target_word_count
)
VALUES
    ('about_lily', 'About Lily AI', 1, TRUE, TRUE, FALSE, NULL, '500-750'),
    ('how_to_use', 'How to Use This Pack', 2, TRUE, TRUE, FALSE, NULL, '500-750'),
    ('introduction', 'Introduction', 3, TRUE, TRUE, TRUE, 'question_breakdown', '500-750'),
    ('topic_analysis', 'Topic Analysis', 4, TRUE, TRUE, TRUE, 'mind_map', '5000-7000'),
    ('methodological_approaches', 'Methodological Approaches', 5, TRUE, TRUE, TRUE, 'journey_map', '3000-4000'),
    ('key_arguments', 'Key Arguments', 6, TRUE, TRUE, TRUE, 'argument_mapping', '5000-7000'),
    ('citations_resources', 'Citations and Resources', 7, TRUE, TRUE, FALSE, NULL, '1000-2000'),
    ('personalized_questions', 'Personalized Questions', 8, TRUE, FALSE, FALSE, NULL, '500-1000'),
    ('appendices', 'Appendices', 9, TRUE, FALSE, FALSE, NULL, '500-1000');
