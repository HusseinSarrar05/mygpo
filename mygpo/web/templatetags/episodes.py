from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils.html import strip_tags, format_html
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.safestring import mark_safe
from django.templatetags.static import static

from mygpo import utils
from mygpo.data.mimetype import get_type, get_mimetype
from mygpo.web.utils import get_episode_link_target

register = template.Library()

# Initialize global coverage data
coverage_data = {
    'Branch 0': 0,
    'Branch 1': 0,
    'Branch 2': 0,
    'Branch 3': 0,
    'Branch 4': 0,
    'Branch 5': 0,
    'Branch 6': 0,
    'Branch 7': 0,
    'Branch 8': 0,
    'Branch 9': 0,
    'Branch 10': 0,
    'Branch 11': 0,
    'Branch 12': 0
}

def initialize_coverage():
    global coverage_data
    for key in coverage_data.keys():
        coverage_data[key] = 0

def get_coverage_data():
    return coverage_data

def write_coverage_to_file(filename, method_name, branch_coverage):
    total = len(branch_coverage)
    num_taken = 0
    with open(filename, 'w') as file:
        file.write(f"FILE: {filename}\nMethod: {method_name}\n")
        for index, (branch, taken) in enumerate(branch_coverage.items()):
            if taken:
                file.write(f"{branch} was taken\n")
                num_taken += 1
            else:
                file.write(f"{branch} was not taken\n")
        file.write("\n")
        coverage_level = num_taken / total * 100
        file.write(f"Total coverage = {coverage_level}%\n")

@register.filter
def episode_status_text(episode, coverage):
    if not episode or not episode.action:
        # Branch ID: 0
        coverage[0] = True
        return ""
    else:
        # Branch ID: 1
        coverage[1] = True
    if episode.action == "new":
        # Branch ID: 2
        coverage[2] = True
        return _("New episode")
    elif episode.action == "download":
        # Branch ID: 3
        coverage[3] = True
        if episode.device.name:
            # Brthianch ID: 4
            coverage[4] = True
            return _("Downloaded to %s") % episode.device.name
        else:
            # Branch ID: 5
            coverage[5] = True
            return _("Downloaded")
    elif episode.action == "play":
        # Branch ID: 6
        coverage[6] = True
        if episode.device.name:
            # Branch ID: 7
            coverage[7] = True
            return _("Played on %s") % episode.device.name
        else:
            # Branch ID: 8
            coverage[8] = True
            return _("Played")
    elif episode.action == "delete":
        # Branch ID: 9
        coverage[9] = True
        if episode.device.name:
            # Branch ID: 10
            coverage[10] = True
            return _("Deleted on %s") % episode.device.name
        else:
            # Branch ID: 11
            coverage[11] = True
            return _("Deleted")
    return _("Unknown status")

@register.filter
def episode_status_icon(action):
    global coverage_data

    if not action or not action.action:
        coverage_data['Branch 0'] += 1 #Branch 1 taken
        s = '<img src="%s" alt="nothing" title="%s" />' % (
            staticfiles_storage.url("nothing.png"),
            _("Unplayed episode"),
        )
    else:
        coverage_data['Branch 1'] += 1 #Branch 2 taken
        date_string = (_(" on %s") % (action.timestamp)) if action.timestamp else ""
        device_string = (_(" on %s") % (action.client.name)) if action.client else ""

        if action.action == "flattr":
            coverage_data['Branch 2'] += 1 #Branch 3 taken
            s = (
                '<img src="https://flattr.com/_img/icons/flattr_logo_16.png" alt="flattr" title="%s" />'
                % (_("The episode has been flattr'd"),)
            )

        elif action.action == "new":
            coverage_data['Branch 3'] += 1 #Branch 4 taken
            s = '<img src="%s" alt="new" title="%s" />' % (
                staticfiles_storage.url("new.png"),
                "%s%s%s"
                % (_("This episode has been marked new"), date_string, device_string),
            )
        elif action.action == "download":
            coverage_data['Branch 4'] += 1 #Branch 5 taken
            s = '<img src="%s" alt="downloaded" title="%s" />' % (
                staticfiles_storage.url("download.png"),
                "%s%s%s"
                % (_("This episode has been downloaded"), date_string, device_string),
            )
        elif action.action == "play":
            coverage_data['Branch 5'] += 1 #Branch 6 taken
            if action.stopped is not None:
                coverage_data['Branch 6'] += 1 #Branch 7 taken
                if getattr(action, "started", None) is not None:
                    coverage_data['Branch 9']+=1 #Branch 10 taken, implicit branch
                    playback_info = _(" from %(start)s to %(end)s") % {
                        "start": utils.format_time(action.started),
                        "end": utils.format_time(action.stopped),
                    }
                else:
                    coverage_data['Branch 10'] += 1 #Branch 11 taken, implicit branch
                    playback_info = _(" to position %s") % (
                        utils.format_time(action.stopped),
                    )
            else:
                coverage_data['Branch 7'] += 1 #Branch 8 taken
                playback_info = ""
            s = '<img src="%s" alt="played" title="%s" />' % (
                staticfiles_storage.url("playback.png"),
                "%s%s%s%s"
                % (
                    _("This episode has been played"),
                    date_string,
                    device_string,
                    playback_info,
                ),
            )
        elif action.action == "delete":
            coverage_data['Branch 8'] += 1 #Branch 9 taken
            s = '<img src="%s" alt="deleted" title="%s" />' % (
                staticfiles_storage.url("delete.png"),
                "%s%s%s"
                % (_("This episode has been deleted"), date_string, device_string),
            )
        else:
            coverage_data['Branch 11'] +=1 # Branch 12 taken, implicit branch
            return action.action  # this is not marked safe by intention
    coverage_data['Branch 12'] +=1 #Branch 13 taken, hidden branch
    return mark_safe(s)


@register.filter
def is_image(episode):
    mimetypes = episode.mimetypes.split(",")
    return any(get_type(mimetype) == "image" for mimetype in mimetypes)


class EpisodeLinkTargetNode(template.Node):
    """Links to a (view of a) Podcast"""

    def __init__(self, episode, podcast, view_name="episode", add_args=[]):
        self.episode = template.Variable(episode)
        self.podcast = template.Variable(podcast)
        self.view_name = view_name.replace('"', "")
        self.add_args = [template.Variable(arg) for arg in add_args]

    def render(self, context):
        episode = self.episode.resolve(context)
        podcast = self.podcast.resolve(context)
        add_args = [arg.resolve(context) for arg in self.add_args]
        return get_episode_link_target(episode, podcast, self.view_name, add_args)

    @staticmethod
    def compile(parser, token):
        try:
            contents = token.split_contents()
            tag_name = contents[0]
            episode = contents[1]
            podcast = contents[2]
            view_name = contents[3] if len(contents) > 3 else "episode"
            add_args = contents[4:]

        except ValueError:
            raise template.TemplateSyntaxError(
                "%r tag requires at least one argument" % token.contents.split()[0]
            )

        return EpisodeLinkTargetNode(episode, podcast, view_name, add_args)


register.tag("episode_link_target", EpisodeLinkTargetNode.compile)


@register.simple_tag
def episode_link(episode, podcast, title=None):
    """Returns the link for a single Episode"""

    title = (
        title
        or getattr(episode, "display_title", None)
        or episode.get_short_title(podcast.common_episode_title)
        or episode.title
        or _("Unknown Episode")
    )

    title = strip_tags(title)

    return format_html(
        '<a href="{target}" title="{title}">{title}</a>',
        target=get_episode_link_target(episode, podcast),
        title=title,
    )


@register.simple_tag
def get_id(obj):
    return obj._id


@register.simple_tag
def episode_number(episode, podcast):
    num = episode.get_episode_number(podcast.common_episode_title)
    return num or ""


@register.simple_tag
def episode_short_title(episode, podcast):
    title = episode.get_short_title(podcast.common_episode_title)
    return title or ""
