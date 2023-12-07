class Query:

    @staticmethod
    def load_v_table():
        sql = """
            MERGE INTO TASKS.TASK_1.V_TABLE
                USING ( 
                SELECT CSV_PARSER.V
                -- Query the stage for one file or use a pattern for multiple
                FROM @TASKS.TASK_1.GCS_STAGE (FILE_FORMAT => TASKS.TASK_1.TEXT_FORMAT, PATTERN=>'.*.csv') STG
                -- Lateral join to call our UDTF
                JOIN LATERAL TASKS.TASK_1.PARSE_CSV(STG.$1, ',', '"') 
                -- Partition by file to support multiple files at once
                OVER (PARTITION BY METADATA$FILENAME 
                -- Order by row number to ensure headers are first in each window
                ORDER BY METADATA$FILE_ROW_NUMBER) AS CSV_PARSER ) AS src ON V_TABLE.v: ID = src.v: ID
                WHEN MATCHED THEN UPDATE SET  V_TABLE.v = src.v
                WHEN NOT MATCHED THEN INSERT (V_TABLE.v) VALUES (src.v);
        """
        return sql

    @staticmethod
    def load_col_table():
        sql = """
            MERGE INTO TASKS.TASK_1.COL_TABLE
                USING TASKS.TASK_1.V_TABLE AS src ON COL_TABLE.ID = src.v:ID::INT
                WHEN MATCHED THEN UPDATE SET  COL_TABLE.METACRITIC_RATING = src.v:METACRITIC_RATING,
                                              COL_TABLE.REVIEWER_RATING = src.v:REVIEWER_RATING,
                                              COL_TABLE.POSITIVITY_RATIO = src.v:POSITIVITY_RATIO                            
                WHEN NOT MATCHED THEN INSERT (COL_TABLE.ID, 
                                              COL_TABLE.NAME, 
                                              COL_TABLE.YEAR, 
                                              COL_TABLE.METACRITIC_RATING, 
                                              COL_TABLE.REVIEWER_RATING,
                                              COL_TABLE.POSITIVITY_RATIO, 
                                              COL_TABLE.TO_BEAT_MAIN, 
                                              COL_TABLE.TO_BEAT_EXTRA, 
                                              COL_TABLE.TO_BEAT_COMPLETIONIST, 
                                              COL_TABLE.EXTRA_CONTENT_LENGTH, 
                                              COL_TABLE.TAGS) 
                                      VALUES (src.v: ID ,
                                              src.v: NAME,
                                              src.v: YEAR,
                                              src.v: METACRITIC_RATING,
                                              src.v: REVIEWER_RATING,
                                              src.v: POSITIVITY_RATIO,
                                              src.v: TO_BEAT_MAIN,
                                              src.v: TO_BEAT_EXTRA,
                                              src.v: TO_BEAT_COMPLETIONIST,
                                              src.v: EXTRA_CONTENT_LENGTH,
                                              src.v: TAGS);
        """
        return sql

    @staticmethod
    def load_max_rating_table():
        sql = """
            MERGE INTO TASKS.TASK_1.RATING_TABLE
                USING (
                SELECT YEAR, 
                       MAX(METACRITIC_RATING) AS max_metacritic_rating, 
                       MAX(REVIEWER_RATING) AS max_reviewer_rating
                FROM TASKS.TASK_1.COL_TABLE
                WHERE YEAR IS NOT NULL
                GROUP BY YEAR 
                ) AS src ON RATING_TABLE.YEAR = src.YEAR
                WHEN MATCHED THEN UPDATE 
                                      SET RATING_TABLE.MAX_METACRITIC_RATING = src.MAX_METACRITIC_RATING 
                WHEN NOT MATCHED THEN INSERT (RATING_TABLE.YEAR, RATING_TABLE.MAX_METACRITIC_RATING, RATING_TABLE.MAX_REVIEWER_RATING )
                                      VALUES (src.YEAR, src.MAX_METACRITIC_RATING, src.MAX_REVIEWER_RATING );
        """
        return sql
