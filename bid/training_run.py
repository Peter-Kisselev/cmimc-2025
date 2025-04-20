from config import *
from training_engine import BidEngine
import optuna

last_best_score = -200
last_best_param = None
def objective(trial):
    global last_best_score, last_best_param
    a = trial.suggest_float('my_score', -5, 5)
    b = trial.suggest_float('my_strong', -5, 5)
    c = trial.suggest_float('my_weak', -5, 5)
    d = trial.suggest_float('opp_strong', -5, 5)
    e = trial.suggest_float('opp_weak', -5, 5)
    f = trial.suggest_float('heavy_auc', -5, 5)

    grading_result = BidEngine.grade(player_classes, num_games=num_games, training_weights=[a,b,c,d,e,f])
    if (grading_result.scores['Trained Player #1'] > last_best_score):
        last_best_score = grading_result.scores['Trained Player #1']
        last_best_param =[a,b,c,d,e,f]
        print(last_best_param)

    return -1*grading_result.scores['Trained Player #1']

if __name__ == "__main__":
    study = optuna.create_study()
    study.enqueue_trial({"my_score":3, "my_strong": -4, 'my_weak':2, "opp_strong":4, "opp_weak":-3, 'heavy_auc':3})
    study.optimize(objective, n_trials=1000)
    last_best = study.best_params
    print(study.best_params)
    t = input()
