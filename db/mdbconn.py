import sqlite3
import datetime
import os

class SqliteDB():
    def __init__(self, db):
        try:
            self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(self.BASE_DIR, db)
            
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database file not found: {db_path}")
                
            self.conn = sqlite3.connect(db_path)
            self.c = self.conn.cursor()
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            raise

    def GetBirth(self, year, month, day):
        try:
            query = "SELECT * FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?"
            self.c.execute(query, (year, month, day))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error in GetBirth: {str(e)}")
            return None

    def GetTime(self, time):
        try:
            jitime = [('子','자'),('丑','축'),('寅','인'),('卯','묘'),('辰','진'),('巳','사'),('午','오'),('未','미'),('申','신'),('酉','유'),('戌','술'),('亥','해')]
            if(time>23 or time<0):
                return ''
            ptime = time+1
            if(ptime==24): ptime=0
            itime = (int)(ptime/2)
            return jitime[itime]
        except Exception as e:
            print(f"Error in GetTime: {str(e)}")
            return None

    def Close(self):
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except Exception as e:
            print(f"Error closing connection: {str(e)}")

    def GetPrevTermsDate(self, year, month, day):
        try:
            terms_list = ('立春','驚蟄','淸明','立夏','芒種','小暑','立秋','白露','寒露','立冬','大雪','小寒')
            placeholders = ','.join(['?'] * len(terms_list))
            query = f"""
                SELECT cd_sy, cd_sm, cd_sd, cd_terms_time FROM calenda_data
                WHERE cd_terms_time IS NOT NULL AND cd_terms_time != 'NULL'
                AND cd_hterms IN ({placeholders})
                AND (cd_sy < ? OR (cd_sy = ? AND (cd_sm < ? OR (cd_sm = ? AND cd_sd < ?))))
                ORDER BY cd_sy DESC, cd_sm DESC, cd_sd DESC LIMIT 1
            """
            self.c.execute(query, (*terms_list, year, year, month, month, day))
            return self.c.fetchone()
        except Exception as e:
            print(f"Error in GetPrevTermsDate: {str(e)}")
            return None

    def GetNextTermsDate(self, year, month, day):
        try:
            terms_list = ('立春','驚蟄','淸明','立夏','芒種','小暑','立秋','白露','寒露','立冬','大雪','小寒')
            placeholders = ','.join(['?'] * len(terms_list))
            query = f"""
                SELECT cd_sy, cd_sm, cd_sd, cd_terms_time FROM calenda_data
                WHERE cd_terms_time IS NOT NULL AND cd_terms_time != 'NULL'
                AND cd_hterms IN ({placeholders})
                AND (cd_sy > ? OR (cd_sy = ? AND (cd_sm > ? OR (cd_sm = ? AND cd_sd > ?))))
                ORDER BY cd_sy ASC, cd_sm ASC, cd_sd ASC LIMIT 1
            """
            self.c.execute(query, (*terms_list, year, year, month, month, day))
            return self.c.fetchone()
        except Exception as e:
            print(f"Error in GetNextTermsDate: {str(e)}")
            return None

    def GetPrevTerms12(self, year, month, day):
        try:
            query = """
                SELECT year, month, day, hterm, terms_time FROM terms12
                WHERE (year < ? OR (year = ? AND (month < ? OR (month = ? AND day < ?))))
                ORDER BY year DESC, month DESC, day DESC LIMIT 1
            """
            self.c.execute(query, (year, year, month, month, day))
            return self.c.fetchone()
        except Exception as e:
            print(f"Error in GetPrevTerms12: {str(e)}")
            return None

    def GetNextTerms12(self, year, month, day):
        try:
            query = """
                SELECT year, month, day, hterm, terms_time FROM terms12
                WHERE (year > ? OR (year = ? AND (month > ? OR (month = ? AND day > ?))))
                ORDER BY year ASC, month ASC, day ASC LIMIT 1
            """
            self.c.execute(query, (year, year, month, month, day))
            return self.c.fetchone()
        except Exception as e:
            print(f"Error in GetNextTerms12: {str(e)}")
            return None
