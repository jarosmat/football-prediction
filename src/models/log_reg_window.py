import create_train_data
import sklearn as sk

def main():
    window_sizes = [3,4,5]
    leagues = ['E0', 'D1']
    seasons = [2021,2122,2223,2324,2425,2526]

    best_model = None
    best_log_loss = 0

    for sz in window_sizes:
        X_data, y_data = create_train_data.create_windows_train_data(leagues, seasons, window=sz)
        X_train, X_validate, y_train, y_validate = sk.model_selection.train_test_split(X_data, y_data)

        col_transform = sk.compose.ColumnTransformer([
            ("one_hot_home", sk.preprocessing.OneHotEncoder(), slice(0,sz)),
            ("poly_home", sk.preprocessing.PolynomialFeatures(degree=2, interaction_only=True), slice(0,sz)),
            ("one_hot_away", sk.preprocessing.OneHotEncoder(), slice(sz,2 * sz)),
            ("poly_away", sk.preprocessing.PolynomialFeatures(degree=2, interaction_only=True), slice(sz,2 * sz))
        ])

        pipe = sk.pipeline.Pipeline([
            ("transformer", col_transform),
            ("model", sk.linear_model.LogisticRegressionCV(Cs=10, l1_ratios=(0,0.5,1), cv=5, scoring='neg_log_loss', n_jobs=8, solver='saga', max_iter=2000))
        ])

        pipe.fit(X_train, y_train)

        pred = pipe.predict_proba(X_validate)
        log_loss = sk.metrics.log_loss(y_validate, pred)

        print(f"window size {sz}, log loss: {log_loss}")

        if best_model is None:
            best_model = pipe
            best_log_loss = log_loss
        elif log_loss < best_log_loss:
            best_model = pipe
            best_log_loss = log_loss

if __name__ == "__main__":
    print("da")
    main()




