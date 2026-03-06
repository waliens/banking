"""ML model training and prediction endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Category, MLModel, Transaction, User
from app.schemas.ml import MLModelResponse, PredictRequest, PredictResponse, PredictionItem, TrainResponse

router = APIRouter()


@router.get("/models", response_model=list[MLModelResponse])
def list_models(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> list[MLModel]:
    return db.query(MLModel).order_by(MLModel.id.desc()).all()


@router.post("/train", response_model=TrainResponse, status_code=status.HTTP_201_CREATED)
def train_model(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> TrainResponse:
    from app.ml.trainer import ModelBeingTrainedError, NotEnoughDataError
    from app.ml.trainer import train_model as do_train

    try:
        model = do_train(db)
    except ModelBeingTrainedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A model is already being trained")
    except NotEnoughDataError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return TrainResponse(model=MLModelResponse.model_validate(model), message="Training complete")


@router.post("/predict", response_model=PredictResponse)
def predict_transactions(
    body: PredictRequest, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> PredictResponse:
    from app.ml.predictor import InferenceError, NoValidModelError, predict_categories

    transactions = db.query(Transaction).filter(Transaction.id.in_(body.transaction_ids)).all()
    if not transactions:
        return PredictResponse(predictions=[])

    try:
        results = predict_categories(db, transactions)
    except NoValidModelError:
        return PredictResponse(predictions=[])
    except InferenceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    category_map = {c.id: c for c in db.query(Category).all()}
    predictions = []
    for tx, (cat_id, prob) in zip(transactions, results):
        cat = category_map.get(cat_id) if cat_id is not None else None
        # If predicted category no longer exists (stale model), return null
        predictions.append(
            PredictionItem(
                transaction_id=tx.id,
                category_id=cat.id if cat else None,
                category_name=cat.name if cat else None,
                category_color=cat.color if cat else None,
                probability=round(prob, 4) if cat else 0.0,
            )
        )

    return PredictResponse(predictions=predictions)
