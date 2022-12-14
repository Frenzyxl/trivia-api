from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import random
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    the_questions = questions[start:end]

    return the_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """

    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route("/categories")
    def get_categories():
        categories = Category.query.all()
        category = {category.id: category.type for category in categories}

        if len(categories) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "categories": category
            }
        )

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route("/questions")
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        questions = paginate_questions(request, selection)
        categories = Category.query.order_by(Category.type).all()

        if len(questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": questions,
                "current_category": None,
                "categories": {category.id: category.type for category in categories},
                "total_questions": len(selection)
            }
        )

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            questions = Question.query.order_by(Question.id).all()

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "total_questions": len(questions)

                }
            )
        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()

        new_question = body.get("question", None)
        the_answer = body.get("answer", None)
        the_category = body.get("category", None)
        difficulty_score = body.get("difficulty", None)

        try:
            question = Question(question=new_question, answer=the_answer, category=the_category,
                                difficulty=difficulty_score)
            question.insert()

            return jsonify(
                {
                    "success": True,
                    "created": question.id,
                    "total_questions": len(Question.query.all())
                }
            )

        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route("/questions/search", methods=["POST"])
    def search_questions():
        body = request.get_json()
        search_term = body.get("searchTerm", None)

        if search_term:
            search_results = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()
            questions = paginate_questions(request, search_results)

            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(search_results),
                'current_category': None
            })
        abort(404)

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route("/categories/<string:category_id>/questions")
    def get_questions_by_category(category_id):

        try:
            selection = Question.query.order_by(Question.id).filter_by(category=category_id).all()
            cat = Category.query.get(int(category_id))

            return jsonify(
                {
                    "success": True,
                    "questions": [select.format() for select in selection],
                    "current_category": cat.type,
                    "total_questions": len(selection)
                }
            )
        except:
            abort(404)

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route('/quizzes', methods=['POST'])
    def quiz():
        # get the question category and the previous question

        try:

            body = request.get_json()

            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(422)

            quiz_category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')

            if quiz_category["type"] == "click":
                available_questions = Question.query.filter(
                    Question.id.notin_(previous_questions)).all()

            else:

                available_questions = Question.query.filter_by(category=quiz_category['id']).filter(
                    Question.id.notin_(previous_questions)).all()

            if len(available_questions) > 0:
                random_index = random.randrange(0, len(available_questions))
                new_question = available_questions[random_index].format()

            else:
                new_question = None

            return jsonify({
                'success': True,
                'question': new_question
            })
        except:
            abort(422)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify(
                {"success": False,
                 "error": 404,
                 "message": "resource not found"
                 }), 404
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify(
                {"success": False,
                 "error": 422,
                 "message": "unprocessable"}), 422
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify(
            {"success": False,
             "error": 400,
             "message": "bad request"}), 400

    @app.errorhandler(405)
    def not_found(error):
        return (
            jsonify(
                {"success": False,
                 "error": 405,
                 "message": "method not allowed"}), 405
        )

    return app
