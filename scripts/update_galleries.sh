for f in static/Graphs/cal65/goodreads*html
do
	cp "$f" goodreads/static/novelty/goodreads
done

for f in static/Graphs/cal65/spotify*html
do
	cp "$f" goodreads/static/novelty/spotify
done

for f in static/Graphs/cal65/netflix*html
do
	cp "$f" goodreads/static/novelty/netflix
done