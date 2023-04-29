for f in goodreads/static/Graphs/cal65/goodreads*html
do
	cp "$f" goodreads/static/admin/img/goodreads
done

for f in goodreads/static/Graphs/cal65/spotify*html
do
	cp "$f" goodreads/static/admin/img/spotify
done

for f in goodreads/static/Graphs/cal65/netflix*html
do
	cp "$f" goodreads/static/admin/img/netflix
done