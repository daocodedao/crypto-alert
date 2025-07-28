# 在文件顶部导入 SQLAlchemy 相关模块
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker, scoped_session
import json
from datetime import datetime
from utils.logger_settings import api_logger
import os
from dotenv import load_dotenv
from model.twitter_entry import TwitterEntry  # 导入 TwitterEntry 模型

# 加载.env文件
load_dotenv()

class DBManager:
    def __init__(self, db_config=None):
        # 如果没有提供配置，从环境变量中读取
        if not db_config:
            self.db_config = {
                'host': os.getenv('DB_HOST', '127.0.0.1'),
                'user': os.getenv('DB_USER', 'root'),
                'password': os.getenv('DB_PASSWORD', ''),
                'database': os.getenv('DB_NAME', 'author_marketing')
            }
        else:
            self.db_config = db_config
        
        # 创建数据库连接URL
        db_url = f"mysql+mysqlconnector://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}/{self.db_config['database']}"
        
        # 创建引擎
        self.engine = create_engine(db_url)
        
        # 创建会话工厂
        self.Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))
    
    def _get_session(self):
        """获取数据库会话"""
        return self.Session()
    
    def close(self):
        """关闭数据库连接"""
        self.Session.remove()
        
    def insert_twitter_entries(self, entries):
        """
        将推特条目信息插入到数据库中。

        :param entries: 包含推特条目信息的列表
        """
        session = self._get_session()
        try:
            new_record_count = 0
            for entry in entries:
                tweet_id = entry['tweet_id']
                existing_entry = session.query(TwitterEntry).filter_by(tweet_id=tweet_id).first()
                if not existing_entry:
                    twitter_entry = TwitterEntry(
                        title=entry['title'],
                        link=entry['link'],
                        description=entry['description'],
                        published=entry['published'],
                        tweet_id=tweet_id,
                        author=entry['author']
                    )
                    session.add(twitter_entry)
                    new_record_count += 1
                else:
                    # 更新现有记录
                    existing_entry.title = entry['title']
                    existing_entry.link = entry['link']
                    existing_entry.description = entry['description']
                    existing_entry.published = entry['published']
                    existing_entry.author = entry['author']
            session.commit()
            api_logger.info(f"成功插入 {new_record_count} 条新记录，更新 {len(entries) - new_record_count} 条重复记录")
        except Exception as e:
            session.rollback()
            api_logger.error(f"数据库操作出错: {e}")
        finally:
            session.close()

    def get_twitter_entries(self):
        """
        从数据库中读取所有推特条目信息。

        :return: 包含推特条目信息的列表
        """
        session = self._get_session()
        try:
            entries = session.query(TwitterEntry).all()
            result = []
            for entry in entries:
                result.append({
                    'id': entry.id,
                    'title': entry.title,
                    'link': entry.link,
                    'description': entry.description,
                    'published': entry.published,
                    'tweet_id': entry.tweet_id,
                    'author': entry.author,
                    'created_at': entry.created_at
                })
            return result
        except Exception as e:
            api_logger.error(f"读取数据库出错: {e}")
            return []
        finally:
            session.close()  