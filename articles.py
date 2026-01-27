"""
Curated reading list for daily tech & philosophy refreshers.
10-15 minute reads on technology, focus, and meaning.
"""
import random
from datetime import date

# Curated articles: (title, url, one-liner)
ARTICLES = [
    (
        "The Technium: What Technology Wants",
        "https://kk.org/thetechnium/what-technology/",
        "Kevin Kelly on technology as an extension of life's evolutionary force."
    ),
    (
        "This Is Water - David Foster Wallace",
        "https://fs.blog/david-foster-wallace-this-is-water/",
        "The power of choosing what to pay attention to in daily life."
    ),
    (
        "Solitude and Leadership",
        "https://theamericanscholar.org/solitude-and-leadership/",
        "William Deresiewicz on why true leadership requires thinking alone."
    ),
    (
        "The Maintenance Race",
        "https://www.worksinprogress.co/issue/the-maintenance-race/",
        "Why maintaining what we build matters more than building new things."
    ),
    (
        "Meditations on Moloch",
        "https://slatestarcodex.com/2014/07/30/meditations-on-moloch/",
        "Scott Alexander on coordination problems and why we can't have nice things."
    ),
    (
        "The Gervais Principle",
        "https://www.ribbonfarm.com/2009/10/07/the-gervais-principle-or-the-office-according-to-the-office/",
        "A ruthlessly honest look at organizational dynamics through The Office."
    ),
    (
        "You and Your Research - Richard Hamming",
        "https://www.cs.virginia.edu/~robins/YouAndYourResearch.html",
        "What separates those who do great work from those who could but don't."
    ),
    (
        "The Bus Ticket Theory of Genius",
        "http://paulgraham.com/genius.html",
        "Paul Graham on obsessive interest as the key ingredient of exceptional work."
    ),
    (
        "The Tyranny of the Marginal User",
        "https://nothinghuman.substack.com/p/the-tyranny-of-the-marginal-user",
        "Why software keeps getting dumbed down and what it means for power users."
    ),
    (
        "Taste for Makers",
        "http://paulgraham.com/taste.html",
        "On developing judgment about what's good in design and creation."
    ),
    (
        "The Age of the Essay",
        "http://paulgraham.com/essay.html",
        "Essays as a way of figuring things out, not just communicating."
    ),
    (
        "Speed Matters",
        "https://jsomers.net/blog/speed-matters",
        "Why being fast changes what you're capable of doing."
    ),
    (
        "The Lesson to Unlearn",
        "http://paulgraham.com/lesson.html",
        "How school trains us to game the system instead of doing real work."
    ),
    (
        "The Pmarca Guide to Personal Productivity",
        "https://pmarchive.com/guide_to_personal_productivity.html",
        "Marc Andreessen's contrarian take on getting things done."
    ),
    (
        "Teach Yourself Programming in Ten Years",
        "https://norvig.com/21-days.html",
        "Peter Norvig on why mastery takes time and why that's okay."
    ),
    (
        "The Cook and the Chef: Musk's Secret Sauce",
        "https://waitbutwhy.com/2015/11/the-cook-and-the-chef-musks-secret-sauce.html",
        "First principles thinking explained through a cooking metaphor."
    ),
    (
        "What You'll Wish You'd Known",
        "http://paulgraham.com/hs.html",
        "Advice for your younger self on what actually matters."
    ),
    (
        "In Praise of Idleness",
        "https://harpers.org/archive/1932/10/in-praise-of-idleness/",
        "Bertrand Russell's 1932 essay on why we should work less."
    ),
    (
        "A Mathematician's Lament",
        "https://www.maa.org/external_archive/devlin/LockshartsLament.pdf",
        "Paul Lockhart on how we've stripped the beauty from mathematics."
    ),
    (
        "Hackers and Painters",
        "http://paulgraham.com/hp.html",
        "What software creators can learn from Renaissance artists."
    ),
    (
        "The Psychology of Human Misjudgment",
        "https://fs.blog/great-talks/psychology-human-misjudgment/",
        "Charlie Munger's masterclass on cognitive biases."
    ),
    (
        "Schlep Blindness",
        "http://paulgraham.com/schlep.html",
        "Why we unconsciously avoid hard but valuable work."
    ),
    (
        "Do Things that Don't Scale",
        "http://paulgraham.com/ds.html",
        "The counterintuitive way to build something big."
    ),
    (
        "The Idea Maze",
        "https://cdixon.org/2013/08/04/the-idea-maze",
        "Chris Dixon on why ideas are less about the destination than the path."
    ),
    (
        "1000 True Fans",
        "https://kk.org/thetechnium/1000-true-fans/",
        "Kevin Kelly on a sustainable creative life without mass scale."
    ),
    (
        "Becoming a Magician",
        "https://autotranslucence.com/2018/03/30/becoming-a-magician/",
        "On finding mentors who make the impossible look easy."
    ),
    (
        "How to Do Great Work",
        "http://paulgraham.com/greatwork.html",
        "Paul Graham's synthesis on what leads to exceptional outcomes."
    ),
    (
        "The Case for Working With Your Hands",
        "https://www.nytimes.com/2009/05/24/magazine/24labor-t.html",
        "Matthew Crawford on the hidden satisfactions of physical craft."
    ),
    (
        "I Will Teach You to Be Rich in One Post",
        "https://www.iwillteachyoutoberich.com/blog/the-1-page-personal-finance-plan/",
        "Ramit Sethi's no-BS personal finance framework."
    ),
    (
        "The Lindy Effect",
        "https://fs.blog/the-lindy-effect/",
        "Why old ideas that survive are likely to keep surviving."
    ),
]


def get_daily_article() -> tuple:
    """
    Get today's article recommendation.
    Uses day of year to rotate through the list consistently.
    """
    day_of_year = date.today().timetuple().tm_yday
    index = day_of_year % len(ARTICLES)
    return ARTICLES[index]


def get_random_article() -> tuple:
    """Get a random article (for on-demand requests)."""
    return random.choice(ARTICLES)


def format_article_block(title: str, url: str, description: str) -> str:
    """Format an article for Slack display."""
    return f":book: *Daily Read (10-15 min):*\n<{url}|{title}>\n_{description}_"
