
try:
    from xmodule.modulestore.django import modulestore
    from opaque_keys.edx.keys import CourseKey, UsageKey
except ImportError as e:
    print("Script must be run from edx shell")
    raise e
store = modulestore()

def hide_in_course(course_key):
    course = store.get_course(course_key)
    wiki_tabs = filter(lambda x: x.type == 'wiki', course.tabs)
    if not wiki_tabs:
        return "No wiki in this course!"
    if len(wiki_tabs) > 1:
         return "Several wiki in course? What?"
    wiki = wiki_tabs[0]
    wiki.is_hidden = True
    store.update_item(course, 0)
    return "Ok"

def main():
    course_summaries = store.get_course_summaries()
    length = len(course_summaries)
    messages = ["Found {} courses...".format(length)]

    for num, summary in enumerate(course_summaries):
        key = summary.id
        key_mes = u"{num}\{max}){name} | {id}".format(
            num=num + 1,
            max=length,
            name=summary.display_name,
            id=str(key))
        res_mes = hide_in_course(key)

        messages.append(key_mes)
        messages.append(res_mes)
        messages.append("==========================")

    for m in messages:
        print(m)
main()
