class WindowModel:
    """
    Model for window of last match results.

    Attributes:
        window_size (int): how many last matches are in the window
        pipeline (sklearn Pipeline): the fitted sklearn Pipeline.
    """

    def __init__(self, window_size: int, pipeline):
        self.window_size = window_size
        self.pipeline = pipeline

    def predict(self, X_data):
        return self.pipeline.predict(X_data)

    def predict_proba(self, X_data):
        return self.pipeline.predict_proba(X_data)
