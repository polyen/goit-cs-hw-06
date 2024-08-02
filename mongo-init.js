db.createUser(
        {
            user: "admin",
            pwd: "root",
            roles: [
                {
                    role: "readWrite",
                    db: "messages_db"
                }
            ]
        }
);