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

    # --- Expanded collection ---
    (
        "Life is Short",
        "http://paulgraham.com/vb.html",
        "Paul Graham on why life is too short to spend on things that don't matter."
    ),
    (
        "Maker's Schedule, Manager's Schedule",
        "http://paulgraham.com/makersschedule.html",
        "Paul Graham on why a single meeting can blow a whole afternoon for a maker."
    ),
    (
        "Keep Your Identity Small",
        "http://paulgraham.com/identity.html",
        "Paul Graham on how the labels you attach to yourself make you dumber."
    ),
    (
        "The Top Idea in Your Mind",
        "http://paulgraham.com/top.html",
        "Paul Graham on how your default thought reveals what actually matters to you."
    ),
    (
        "How to Think for Yourself",
        "http://paulgraham.com/think.html",
        "Paul Graham on independent-mindedness and how to cultivate it."
    ),
    (
        "Putting Ideas into Words",
        "http://paulgraham.com/words.html",
        "Paul Graham on why writing is not just a way to communicate but a way to think."
    ),
    (
        "What I Worked On",
        "http://paulgraham.com/worked.html",
        "Paul Graham's autobiography tracing his path from painting to Lisp to Y Combinator."
    ),
    (
        "Cities and Ambition",
        "http://paulgraham.com/cities.html",
        "Paul Graham on how great cities send you a message about what kind of ambition matters."
    ),
    (
        "Mean People Fail",
        "http://paulgraham.com/mean.html",
        "Paul Graham on why being mean makes you stupid and limits what you can build."
    ),
    (
        "The Tail End",
        "https://waitbutwhy.com/2015/12/the-tail-end.html",
        "Tim Urban on visualizing how little time you have left with the people you love."
    ),
    (
        "Your Life in Weeks",
        "https://waitbutwhy.com/2014/05/life-weeks.html",
        "Tim Urban on seeing your entire life as a grid of weeks — most already gone."
    ),
    (
        "Why Procrastinators Procrastinate",
        "https://waitbutwhy.com/2013/10/why-procrastinators-procrastinate.html",
        "Tim Urban on the Instant Gratification Monkey and the Panic Monster in your brain."
    ),
    (
        "How to Pick a Career (That Actually Fits You)",
        "https://waitbutwhy.com/2018/04/picking-career.html",
        "Tim Urban on the Yearning Octopus and first-principles career thinking."
    ),
    (
        "I Can Tolerate Anything Except The Outgroup",
        "https://slatestarcodex.com/2014/09/30/i-can-tolerate-anything-except-the-outgroup/",
        "Scott Alexander on why tolerance is hardest for those closest to us, not farthest."
    ),
    (
        "Considerations on Cost Disease",
        "https://slatestarcodex.com/2017/02/09/considerations-on-cost-disease/",
        "Scott Alexander on why everything — healthcare, education, housing — keeps getting more expensive."
    ),
    (
        "Book Review: Seeing Like a State",
        "https://slatestarcodex.com/2017/03/16/book-review-seeing-like-a-state/",
        "Scott Alexander on why top-down plans by governments fail in predictable ways."
    ),
    (
        "How To Be Successful",
        "https://blog.samaltman.com/how-to-be-successful",
        "Sam Altman's 13 principles for achieving outlier success."
    ),
    (
        "The Days Are Long but the Decades Are Short",
        "https://blog.samaltman.com/the-days-are-long-but-the-decades-are-short",
        "Sam Altman's life advice written on his 30th birthday."
    ),
    (
        "How to Get Rich (Without Getting Lucky)",
        "https://nav.al/rich",
        "Naval Ravikant's expanded tweetstorm on wealth, leverage, and specific knowledge."
    ),
    (
        "The Premium Mediocre Life of Maya Millennial",
        "https://www.ribbonfarm.com/2017/08/17/the-premium-mediocre-life-of-maya-millennial/",
        "Venkatesh Rao on the lifestyle class between genuine and fake, aspiration and coping."
    ),
    (
        "Aggregation Theory",
        "https://stratechery.com/2015/aggregation-theory/",
        "Ben Thompson on how the internet enables platforms to dominate by owning demand."
    ),
    (
        "Choose Boring Technology",
        "https://mcfunley.com/choose-boring-technology",
        "Dan McKinley on why every company gets only three innovation tokens to spend."
    ),
    (
        "The Bitter Lesson",
        "http://www.incompleteideas.net/IncIdeas/BitterLesson.html",
        "Rich Sutton on why scaling computation always beats hand-crafted knowledge in AI."
    ),
    (
        "Spaced Repetition for Efficient Learning",
        "https://gwern.net/spaced-repetition",
        "Gwern on the science and practice of remembering anything forever."
    ),
    (
        "Why Books Don't Work",
        "https://andymatuschak.org/books/",
        "Andy Matuschak on how books rely on a theory of learning that is plainly false."
    ),
    (
        "Going Critical",
        "https://meltingasphalt.com/interactive/going-critical/",
        "Kevin Simler's interactive essay on network dynamics, diffusion, and how ideas spread."
    ),
    (
        "Learnable Programming",
        "https://worrydream.com/LearnableProgramming/",
        "Bret Victor on designing programming environments that let you see and understand code."
    ),
    (
        "The Crossroads of Should and Must",
        "https://medium.com/@elleluna/the-crossroads-of-should-and-must-90c75eb7c5b0",
        "Elle Luna on the difference between what others expect and what you feel called to do."
    ),
    (
        "The Intellectual Yet Idiot",
        "https://medium.com/incerto/the-intellectual-yet-idiot-13211e2d0577",
        "Nassim Taleb on the class of people who are educated beyond their intelligence."
    ),
    (
        "There's No Speed Limit",
        "https://sive.rs/kimo",
        "Derek Sivers on the teacher who showed him the standard pace is for chumps."
    ),
    (
        "Fast",
        "https://patrickcollison.com/fast",
        "Patrick Collison's curated examples of people accomplishing ambitious things quickly."
    ),
    (
        "Marginal Gains: This Coach Improved Every Tiny Thing by 1 Percent",
        "https://jamesclear.com/marginal-gains",
        "James Clear on how British Cycling's 1% improvements led to Olympic dominance."
    ),
    (
        "The Three Sides of Risk",
        "https://collabfund.com/blog/the-three-sides-of-risk/",
        "Morgan Housel on the odds, the average consequences, and the tail-end consequences of risk."
    ),
    (
        "The Psychology of Money",
        "https://collabfund.com/blog/the-psychology-of-money/",
        "Morgan Housel on why financial success is more about behavior than intelligence."
    ),
    (
        "Things You Should Never Do, Part I",
        "https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/",
        "Joel Spolsky on why rewriting software from scratch is almost always a mistake."
    ),
    (
        "Fire and Motion",
        "https://www.joelonsoftware.com/2002/01/06/fire-and-motion/",
        "Joel Spolsky on the art of moving forward every day and not getting pinned down."
    ),
    (
        "Politics is the Mind-Killer",
        "https://www.lesswrong.com/posts/9weLK2AJ9JEt2Tt8f/politics-is-the-mind-killer",
        "Eliezer Yudkowsky on why political topics shut down rational thinking."
    ),
    (
        "The Rise and Fall of Peer Review",
        "https://www.experimental-history.com/p/the-rise-and-fall-of-peer-review",
        "Adam Mastroianni on why science's 60-year experiment with peer review has failed."
    ),
]


def get_daily_article() -> tuple:
    """
    Get today's article recommendation.
    Uses a seeded shuffle per cycle so the order isn't linear
    but is still deterministic (same article all day).
    """
    n = len(ARTICLES)
    day_of_year = date.today().timetuple().tm_yday
    cycle = day_of_year // n
    position = day_of_year % n

    # Seed shuffle with the cycle number — each full pass gets a new order
    rng = random.Random(cycle)
    indices = list(range(n))
    rng.shuffle(indices)

    return ARTICLES[indices[position]]


def get_random_article() -> tuple:
    """Get a random article (for on-demand requests)."""
    return random.choice(ARTICLES)


def get_random_article_excluding(exclude_titles: list) -> tuple:
    """Get a random article, avoiding recently seen titles."""
    available = [a for a in ARTICLES if a[0] not in exclude_titles]
    # If all have been seen, reset and pick from full list
    if not available:
        available = ARTICLES
    return random.choice(available)


def format_article_block(title: str, url: str, description: str) -> str:
    """Format an article for Slack display."""
    return f":book: *Daily Read (10-15 min):*\n<{url}|{title}>\n_{description}_"
