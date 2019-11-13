 DROP TABLE IF EXISTS invitations; DROP TABLE IF EXISTS images; DROP TABLE IF
EXISTS slack_users; DROP TABLE IF EXISTS events;   CREATE TABLE slack_users (
	slack_id VARCHAR(200) NOT NULL PRIMARY KEY,   current_username
	VARCHAR(200) NOT NULL,   first_seen DATE NOT NULL DEFAULT
	CURRENT_TIMESTAMP,   active_ VARCHAR(50) NOT NULL DEFAULT 'true' );
	CREATE TABLE events (   id UNIQUEIDENTIFIER PRIMARY KEY default
		NEWID(),   time DATETIME NOT NULL,   place VARCHAR(200) NOT
		NULL,   finalized VARCHAR(50) NOT NULL DEFAULT 'false' );
	CREATE TABLE invitations (   event_id UNIQUEIDENTIFIER REFERENCES
		events (id),   slack_id VARCHAR(200) REFERENCES slack_users
		(slack_id),   invited_at DATETIME NOT NULL DEFAULT
		CURRENT_TIMESTAMP,   rsvp VARCHAR(100) NOT NULL DEFAULT
		'unanswered',   reminded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,   PRIMARY KEY (event_id, slack_id));
	CREATE TABLE images (   cloudinary_id VARCHAR(200) PRIMARY KEY,
		uploaded_by VARCHAR(200) REFERENCES slack_users (slack_id),
		uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,   title
		VARCHAR(200) );
