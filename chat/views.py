from django.shortcuts import redirect, render

from accounts.decorators import customer_required

from .generation import generate_answer
from .retrieval import context_sources, get_customer_context


MAX_HISTORY_MESSAGES = 20
MAX_QUESTION_LENGTH = 1000


@customer_required
def chat(request):
    history = request.session.get('chat_history', [])

    if request.method == 'POST':
        if 'clear' in request.POST:
            request.session['chat_history'] = []
            request.session.modified = True
            return redirect('chat:home')

        question = request.POST.get('question', '').strip()
        if len(question) > MAX_QUESTION_LENGTH:
            question = question[:MAX_QUESTION_LENGTH]

        if question:
            context = get_customer_context(request.user.customer)
            llm_history = [{'role': m['role'], 'content': m['content']} for m in history]
            try:
                answer = generate_answer(question, context, llm_history)
                sources = context_sources(context)
                history.append({'role': 'user', 'content': question})
                history.append({'role': 'assistant', 'content': answer, 'sources': sources})
            except Exception:
                history.append({'role': 'user', 'content': question})
                history.append({
                    'role': 'assistant',
                    'content': 'Sorry, I could not process your question right now. Please try again.',
                    'sources': [],
                    'error': True,
                })

            if len(history) > MAX_HISTORY_MESSAGES:
                history = history[-MAX_HISTORY_MESSAGES:]

            request.session['chat_history'] = history
            request.session.modified = True
        return redirect('chat:home')

    return render(request, 'chat/chat.html', {'history': history})
