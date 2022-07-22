# Concept
I began this project initially to analyze my own book reading history. After years where I absorbed information largely through podcasts, websites and conversations, reading was becoming more and more important to me. I don't read particularly fast, and each finished book felt like an achievement. I started by creating a spreadsheet to track the books I'd read and slowly filled it in and added more fields I found interesting, such as number of pages and the nationality of the author.

Later I discovered the book cataloguing website Goodreads. I realized here was a data repository that would have the data fields I wanted, as well as interesting new crowd-sourced insights made possible only by mass adoption. This includes the "shelf names", user-defined genres, as well as readership numbers. Goodreads allows users to export their books data, but it does not include a lot of these more insightful fields. I started building a pipeline to scrape those additional fields, and later added functions to look up the gender (via Wikipedia) and nationality (via Google) of the author. The pipeline generates plots of the reading data including a map of world authors and a plot facetted by popularity (the number of other users who have added this book to their account). I have been able to refine the graphs and the code with the help of a number of friends who have exported me their Goodreads data.

![Summary](goodreads/static/admin/img/Summary_plot.jpeg)

Data is neutral. The graphs simply present truth about what a person has read, putting the books in a context that is likely novel to the reader. I believe some people will look at their graphs and find some confirmation about their patterns and interests and perhaps some surprises. Some may see genres that they have not read, nationalities that they have not read, and be inspired to search for books they would have never searched for. Some will feel a sense of achievement for the diligence of their past selves - some will feel motivated to read more.

![Author Map](goodreads/Graphs/static/cal/nationality_map_cal.jpeg)

How popular are the books you read? Do you have a mix of obscure books and bestsellers?

[!Popularity Spectrum](goodreads/static/Graphs/cal/popularity_spectrum_cal.jpeg)

Novelty Insights is the modern anti-bias tool to return the value of your data to you.
