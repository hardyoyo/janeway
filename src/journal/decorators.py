from django.shortcuts import redirect, reverse


def frontend_enabled(func):
    """
    If journal.disable_front_end is enabled this decorator redirects to the
    submission page.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def frontend_enabled_wrapper(request, *args, **kwargs):
        if request.journal and not request.journal.disable_front_end:
            return func(request, *args, **kwargs)

        return redirect(
            reverse(
                'journal_submissions'
            )
        )

    return frontend_enabled_wrapper
