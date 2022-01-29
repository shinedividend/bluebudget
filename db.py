from mysql.connector import connect
from mysql.connector.cursor_cext import CMySQLCursor
from mysql.connector.errors import Error
import json

class PortfolioDB:
    
    def __init__(self, auth, dbname):
        self.auth = auth
        self.dbname = dbname

    
    def is_portfolio_exists(self, portfolio_name: str):
        try:
            with connect(username=self.auth['username'], password=self.auth['password'], database=self.dbname) as db:
                cursor: CMySQLCursor = db.cursor()
                query = "SELECT name FROM portfolio WHERE name LIKE %s"
                cursor.execute(query, (portfolio_name, ))
                result = cursor.fetchone()
                return False if result is None else True
        except Error as e:
            raise e

    def insert_portfolio(self, portfolio_name: str, funds: float):
        is_exists = self.is_portfolio_exists(portfolio_name)
        if is_exists:
            raise PortfolioAlreadyExistsException('Porfolio already exists.')
        with connect(username=self.auth['username'], password=self.auth['password'], database=self.dbname) as db:
            cursor: CMySQLCursor = db.cursor()
            query = "INSERT INTO portfolio(name, stocks_data) VALUES(%s, %s)"
            portfolio_data = {}
            portfolio_data['funds'] = funds
            cursor.execute(query, (portfolio_name, json.dumps(portfolio_data)))
            db.commit()
    
    def remove_portfolio(self, portfolio_name: str):
        is_exists = self.is_portfolio_exists(portfolio_name)
        if not is_exists:
            raise PortfolioNotFoundException
        with connect(username=self.auth['username'], password=self.auth['password'], database=self.dbname) as db:
            cursor: CMySQLCursor = db.cursor()
            query = "DELETE FROM portfolio WHERE name LIKE %s"
            cursor.execute(query, (portfolio_name, ))
            db.commit()
            return True
    
    def get_portfolio_data(self, portfolio_name: str):
        is_exists = self.is_portfolio_exists(portfolio_name)
        if not is_exists:
            raise PortfolioNotFoundException
        with connect(username=self.auth['username'], password=self.auth['password'], database=self.dbname) as db:
            cursor: CMySQLCursor = db.cursor()
            query = "SELECT stocks_data FROM portfolio WHERE name LIKE %s"
            cursor.execute(query, (portfolio_name, ))
            result = cursor.fetchone()
            if result is None:
                raise PortfolioNotFoundException
            return json.loads(result[0])
    
    def add_portfolio_funds(self, portfolio_name: str, to_add_funds: float):
        is_exists = self.is_portfolio_exists(portfolio_name)
        if not is_exists:
            raise PortfolioNotFoundException
        portfolio_data = self.get_portfolio_data(portfolio_name)
        if portfolio_data.get('funds', None) is None:
            portfolio_data['funds'] = to_add_funds
        else:
            portfolio_data['funds'] += to_add_funds
        with connect(username=self.auth['username'], password=self.auth['password'], database=self.dbname) as db:
            cursor: CMySQLCursor = db.cursor()
            query = "UPDATE portfolio SET stocks_data=%s WHERE name LIKE %s"
            cursor.execute(query, (json.dumps(portfolio_data), portfolio_name))
            db.commit()
    
    def get_portfolio_names(self):
           with connect(username=self.auth['username'], password=self.auth['password'], database=self.dbname) as db:
               cursor: CMySQLCursor = db.cursor()
               query = "SELECT name from portfolio"
               cursor.execute(query)
               return [row[0] for row in cursor]
         
class PortfolioAlreadyExistsException(Exception):
    pass


class PortfolioNotFoundException(Exception):
    pass
    