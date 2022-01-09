from celery import Celery




def make_celery(app):
    celery = Celery(
      app.import_name,
      backend=app.config['CELERY_RESULT_BACKEND'],
      broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
      def __init__(self):
        super().__init__()
        from db.database import init_db
        self._session_class, self._engine = init_db()
        self._session = None
      
      def after_return(self, *args, **kwargs):
        if self._session is not None:
          self._session.remove()

      @property
      def session(self):
        if self._session is None:
          self._session = self._session_class()
        return self._session

      def __call__(self, *args, **kwargs):
        with app.app_context():
          return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery