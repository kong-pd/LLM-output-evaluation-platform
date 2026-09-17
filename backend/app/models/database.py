import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


def generate_id():
    return uuid.uuid4().hex[:12]


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True, default=generate_id)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    total_items = Column(Integer, default=0)
    evaluated_items = Column(Integer, default=0)
    annotated_items = Column(Integer, default=0)
    status = Column(String, default="uploaded")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    items = relationship("EvalItem", back_populates="dataset", cascade="all, delete-orphan")


class EvalItem(Base):
    __tablename__ = "eval_items"
    id = Column(String, primary_key=True, default=generate_id)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    row_index = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    context = Column(Text, default="")
    llm_answer = Column(Text, nullable=False)
    auto_faithfulness = Column(Float, nullable=True)
    auto_relevance = Column(Float, nullable=True)
    auto_coherence = Column(Float, nullable=True)
    auto_context_relevance = Column(Float, nullable=True)
    auto_groundedness = Column(Float, nullable=True)
    auto_error_type = Column(String, nullable=True)
    auto_eval_status = Column(String, default="pending")
    auto_eval_model = Column(String, nullable=True)
    auto_eval_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    dataset = relationship("Dataset", back_populates="items")
    annotations = relationship("Annotation", back_populates="eval_item", cascade="all, delete-orphan")


class Annotation(Base):
    __tablename__ = "annotations"
    id = Column(String, primary_key=True, default=generate_id)
    eval_item_id = Column(String, ForeignKey("eval_items.id"), nullable=False)
    dimension = Column(String, nullable=False)
    auto_score = Column(Float, nullable=False)
    human_score = Column(Float, nullable=False)
    action = Column(String, nullable=False)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    eval_item = relationship("EvalItem", back_populates="annotations")


DATABASE_URL = "sqlite:///./llm_eval.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
