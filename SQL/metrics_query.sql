-- Query 1: Count users per variant
SELECT variant
    Count(*) AS num_users
From experiment_assignments
GROUP BY variant;

-- Query 2: Count purchases per variant 
SELECT
    ea.variant,
    COUNT (DISTINCT s.session_id) AS total_sessions,
    COUNT (DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.session_id END) AS purchases
FROM experiment_assignments ea
JOIN sessions s ON ea.user_id = s.user_id
JOIN events e ON s.session_id = e.session_id
GROUP BY ea.variant;

-- Query 3: Build full metrics dataset
SELECT
    ea.variant,
    s.session_id,
    s.device,
    u.country,
    MAX(CASE WHEN e.event_type = 'page_view' THEN 1 ELSE 0 END) AS viewed,
    MAX(CASE WHEN e.event_type = 'click' THEN 1 ELSE 0 END) AS clicked,
    MAX(CASE WHEN e.event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS added_to_cart,
    MAX(CASE WHEN e.event_type = 'purchase' THEN 1 ELSE 0 END) AS purchased
FROM experiment_assignments ea
JOIN sessions s ON ea.user_id = s.user_id
JOIN events e ON s.session_id = e.session_id
JOIN users u ON s.user_id = u.user_id
GROUP BY ea.variant, s.session_id;
