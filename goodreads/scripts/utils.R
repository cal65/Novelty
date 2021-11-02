options(stringsAsFactors = F)
library(ggplot2)
library(data.table)
library(ggrepel)
library(forcats)
library(plyr)
library(stringi)
library(rworldmap)
library(RColorBrewer)

preprocess <- function(dt){
  dt$gender <- mapvalues(dt$gender,
                                       from = c('mostly_male', 'mostly_female'),
                                       to = c('male', 'female'), warn_missing = FALSE)
  names(dt) <- gsub(' ', '.', names(dt))
  dt$date_read <- as.Date(dt$date_read, format = '%Y-%m-%d')
  dt$title.simple <- gsub(':.*', '', dt$title)
  dt$title.simple <- gsub('\\(.*\\)', '', dt$title.simple)
  
  return(dt)
}

narrative <- function(dt){
  shelf_columns = grep('shelf', names(dt), value=T)
  dt$Narrative <- apply(
    dt, 1, function(x) ifelse(any(
    grepl('Nonfiction|Memoir', x[shelf_columns])
    ), 'Nonfiction', 'Fiction')
  )
  return(dt)
}

read_percentage <- function(dt){
  # It seems sometimes the "added by" value is off by a factor of 10. When the 
  # number of people listing the book as "to read" is larger than total added by, multiply by 10
  dt[to_reads > added_by, added_by := added_by * 10] 
  dt$read <- with(dt, added_by - to_reads)
  dt$read.percentage <- with(dt, read / added_by)
  
  return(dt)
}

run_all <- function(df){
  dt <- preprocess(df)
  dt <- narrative(dt)
  dt <- read_percentage(dt)
  return(dt)
}

preprocess_dt <- function(dt){
  dt <- dt[Title != '']
  dt$added_by[is.na(dt$added_by)] <- 0
  dt$to_reads[is.na(dt$to_reads)] <- 0
  dt$Edition_published <- unlist(lapply(str_extract_all(dt$date_published, '[0-9]{4}') , function(x) x[1]))
  dt$Edition_published <- as.numeric(dt$Edition_published)
  dt$Original.Publication.Year <- unlist(lapply(str_extract_all(dt$Publish_info, 'first published .*') , 
                                                    function(x) x[1]))
  dt$Original.Publication.Year <- unlist(lapply(str_extract_all(dt$Original.Publication.Year, '[0-9]{4}') , 
                                                    function(x) x[1]))
  dt$Original.Publication.Year <- as.numeric(dt$Original.Publication.Year)
  dt$Original.Publication.Year <- ifelse(!is.na(dt$Original.Publication.Year), 
                                             dt$Original.Publication.Year,
                                             dt$Edition_published)
  
  dt <- unique(dt)
  
  dt$Source <- 'Random Scraped'
  dt$Exclusive.Shelf <- 'read'
}


month_plot <- function(df, name, date_col, page_col, title_col,
                       author_gender_col, lims=NULL, save=F){
  setDT(df)
  df$year_read <- as.numeric(format(df[[date_col]], '%Y'))
  df$Month.Read  <- as.numeric(format(df[[date_col]], '%m'))
  if (length(unique(df$year_read)) < 1) {
    return()
  }
  df <- df[!is.na(year_read)]
  if (!is.null(lims)){
    df <- df[year_read > lims[1] & year_read < lims[2]]
  }
  ggplot(df, 
         aes(x=Month.Read, y=get(page_col), group=fct_rev(fct_inorder(get(title_col))))) + 
    geom_col(aes(fill=get(author_gender_col)), width=1, alpha=0.65, color='black') + 
    facet_grid(year_read ~ .) +
    scale_fill_brewer('Author Gender', palette = 'Pastel1', guide = "none") +
    scale_color_brewer('Type', palette = 'Dark2') +
    scale_linetype_discrete('Type') +
    geom_text(aes(label=Author), position = position_stack(0.5), 
              size=2.5, fontface='bold') +
    scale_x_continuous(breaks=1:12, labels=1:12) +
    ggtitle(paste0('Month Breakdown - ', name)) + 
    xlab('Month') + ylab('Number of Pages') + 
    theme(strip.text.y=element_text(angle=0), plot.title = element_text(hjust=0.5),
          panel.background = element_rect(color='black', fill=NA))
  if (save == T){
    ggsave(paste0('Novelty/goodreads/static/Graphs/', name, '/Monthly_pages_read_', name, '.jpeg'), width=15, height=9, dpi=180)
  }
}

year_plot <- function(df, name, fiction_col, date_col, page_col, 
                      title_col, author_gender_col, str_len=30, start_year = 2010,
                      save=F){
  divergent_df <- df
  divergent_df$Pages <- with(divergent_df, ifelse(get(fiction_col) == 'Fiction', -1*get(page_col), get(page_col)))
  str_len <- str_len
  divergent_df$year_read <- format(divergent_df[[date_col]], '%Y')
  # exit function if there is no date data
  if (length(unique(divergent_df$year_read)) < 1) {
    return()
  }
  divergent_df[[title_col]] <- sapply(divergent_df[[title_col]],
                               function(x) paste(stri_wrap(x, width=str_len), collapse='\n'))
  ggplot(divergent_df[year_read >= start_year], aes(x=year_read, y=Pages, group=fct_rev(fct_inorder(get(title_col))))) +
    geom_col(aes(color=get(fiction_col), fill=get(author_gender_col)), 
             size=0.7, width = .7, alpha=0.7) +
    geom_hline(yintercept=0, linetype='solid', size=1, color='white') +
    geom_text(aes(label=get(title_col)), position = position_stack(0.5), size=1.5) +
    scale_color_manual(values=c('chartreuse', 'Grey'), 'Narrative') + 
    scale_fill_brewer(palette='Dark2', 'Author Gender') +
    xlab('Year Read') +
    ggtitle(paste0(name, ' - Reading History')) +
    theme_pander() + theme(plot.title=element_text(hjust=0.5), 
                           legend.position = 'bottom') 
  if (save == T){
    ggsave(paste0('Novelty/goodreads/static/Graphs/',  name, '/Yearly_pages_read_', name, '.jpeg'), width=15, height=9)
  }
}

generate_labels <- function(breaks){
  if (length(breaks) == 2){
    return (paste0(breaks[1], ' - ', breaks[2]))
  }
  else {
    return (c(paste0(breaks[1], ' - ', breaks[2]), generate_labels(breaks[-1])))
  }
}

read_plot <- function(df, 
                      name, 
                      read_col, 
                      title_col, 
                      min_break = 3, 
                      plot=F, 
                      plot_name = 'popularity_spectrum_',
                      date_col='date_read',
                      start_year=NA){
  max_read <- as.integer(max(df[[read_col]], na.rm=T))
  df <- df[!is.na(get(read_col))]
  if (!is.na(start_year)){
    start_date <- as.Date(paste0(start_year, '-01-01'))
    df <- df[get(date_col) > start_date]
  }
  # control text sizes
  max_digits <- nchar(as.character(max_read)) + 1
  breaks <- c(0, 10^c(min_break : max_digits))
  df[[read_col]] <- as.numeric(df[[read_col]])
  df$title_length <- nchar(df[[title_col]])
  df$text_size <- pmax(3, 70/df$title_length)
  # order title text by popularity
  df <- df[order(get(read_col))]
  df[[title_col]] <- factor(df[[title_col]], levels = unique(df[[title_col]]))
  labels = generate_labels(prettyNum(breaks, big.mark = ',', scientific=F))
  df$strats <- cut(df[[read_col]], breaks = breaks, 
                   labels = labels)
  ggplot(df, aes(x=strats, y=get(title_col))) +
    geom_tile(aes(fill=Narrative), color='black') +
    geom_text(aes(label = get(title_col), size = text_size)) +
    facet_wrap(strats ~ ., scales='free', nrow=1) +
    scale_fill_manual(values = c('hotpink2', 'darkolivegreen')) +
    scale_size_continuous(guide = "none", range=c(3, 10)) +
    xlab('Number of Readers') + 
    ylab('Title') +
    ggtitle(paste0('Readership Spectrum - ', name)) +
    theme(axis.text.y = element_blank(),
          plot.title = element_text(hjust=0.5),
          panel.background = element_blank())
  if (plot){
    ggsave(paste0('Novelty/goodreads/static/Graphs/', name, '/', plot_name, name, '.jpeg'), width = 16, height=9)
  }
}

### % finish plot
finish_plot <- function(df, 
                      name, 
                      read_col = 'read.percentage',
                      n = 10, 
                      plot=F, 
                      plot_name = 'finish_plot_'){
  df_read <- df[order(get(read_col)),]
  df_read <- df_read[!is.na(get(read_col))]
  # keep only bottom n
  df_read <- head(df_read, n)
  df_read$title.simple <- factor(df_read$title.simple,
                                 levels = unique(df_read$title.simple))
  ggplot(df_read, aes(x=title.simple)) +
    geom_col(aes( y=1), fill='Dark Blue') +
       geom_col(aes( y=get(read_col)), fill='red') +
    geom_text(aes(y=get(read_col)/2, label = paste0(read, ' / ', added_by)), 
              size=n * 3/5, color='white', hjust=0) +
    ylim(0, 1) +
    xlab('Title') +
    ylab('Reading Percentage') +
       coord_flip() + 
       ggtitle('Least Finished Reads') +
       theme_pander() +
       theme(plot.title = element_text(hjust=0.5))
  if (plot == T){
    ggsave(paste0('Novelty/goodreads/static/Graphs/', name, '/', plot_name, name, '.jpeg'), width=12, height=8)
  }
}

year_comparison <- function(l, year_col, year_start, user, plot=T) {
  l_df <- setDT(do.call('rbind.fill', l))
  year_max <- max(l_df[,get(year_col)], na.rm=T)
  den_all <- density(l_df[!is.na(get(year_col)),][,get(year_col)], 
          from = year_start, to = year_max)
  den_user <- density(l[[user]][!is.na(get(year_col)),][,get(year_col)], 
                      from = year_start, to = year_max)
  density_df <- data.frame(x=den_all$x, y_all=den_all$y, y_user= den_user$y)
  names(density_df) <- mapvalues(names(density_df), 
                                 from = 'y_user', to = paste0('y_', user))
  density_df$y_diff <- with(density_df, get(paste0('y_', user)) - y_all)
  density_df.m <- reshape2::melt(density_df, id = 'x', variable.name = 'Source')
  density_df.m$Source <- gsub('y_', '', density_df.m$Source)
  density_df.m$Source <- factor(density_df.m$Source, levels = unique(density_df.m$Source))
  ggplot(density_df.m) +
    geom_area(aes(x=x, y=value, fill=Source)) +
    facet_grid(Source ~ .) +
    scale_fill_brewer(palette = 'Pastel1') +
    xlab(gsub('.', ' ', year_col)) + 
    theme_dark() +
    ggtitle('Publication Year Comparison')
  if (plot == T){
    ggsave(paste0('Novelty/goodreads/static/Graphs/', user, '/publication_year_', user, '.jpeg'), width=12, height=8)
  }
}

update_authors_artifact <- function(artifact, df_new, id_col='Author', gender_col='gender', title_col='Title'){
  setDT(artifact)
  setDT(df_new)
  df_new_authors <- df_new[, .(Title=head(get(title_col),1)), by = c(id_col, gender_col)]
  authors_new = df_new_authors[!get(id_col) %in% artifact[,get(id_col)]]
  names(authors_new) <- mapvalues(names(authors_new), from='gender', to='gender_guessed')
  authors_new$gender_fixed <- authors_new$gender_guessed
  authors_new$Country.Chosen <- ''
  write.csv(authors_new, 'goodreads/scripts/new_authors_data.csv', row.names=F)
  system('/home/bitnami/Reading-History/Novelty/env/bin/python goodreads/scripts/google_answer.py goodreads/scripts/new_authors_data.csv')
  system('/home/bitnami/Reading-History/Novelty/env/bin/python goodreads/scripts/choose_nationality.py goodreads/scripts/new_authors_data.csv')
  system('/home/bitnami/Reading-History/Novelty/env/bin/python goodreads/scripts/wikipedia.py goodreads/scripts/new_authors_data.csv')
  # system('/Users/apple/opt/anaconda3/bin/python goodreads/scripts/google_answer.py goodreads/scripts/new_authors_data.csv')
  # system('/Users/apple/opt/anaconda3/bin/python goodreads/scripts/choose_nationality.py goodreads/scripts/new_authors_data.csv')
  # system('/Users/apple/opt/anaconda3/bin/python goodreads/scripts/wikipedia.py goodreads/scripts/new_authors_data.csv')
  new_data <- read.csv('goodreads/scripts/new_authors_data.csv')
  artifact <- rbind.fill(artifact, new_data)
  # because of the multiple programming languages, have this awkward write python read pipeline
  write.csv(artifact, 'goodreads/scripts/authors_database.csv', row.names=F)
  return (artifact)
}

merge_nationalities <- function(df, authors_db, country_col = 'Country.Chosen'){
  df <- merge(df, authors_db[,c('author_name', country_col), with=F], by.x='author', by.y='author_name', all.x=T)
  return (df)
}

plot_map_data <- function(df, region_dict, world_df, user, country_col = 'nationality_chosen'){
  print(df)
  country_df <- merge(df, region_dict, by.x='nationality_chosen', by.y='nationality', all.x=T)
  regions_count <- data.frame(table(country_df$region))
  names(regions_count) <- c('region', 'count')
  world_df <- merge(world_df, regions_count, all.x=T)
  max_count = max(regions_count$count)
  my_breaks <- c(1, rep(2^(1:round(log2(max_count)))))
  ggplot(world_df) + 
    geom_polygon((aes(x=long, y=lat, group=group, fill=count))) +
    scale_fill_gradientn(name = "count", trans = "log", breaks=my_breaks,
                        colors=rev(brewer.pal(8, 'RdBu'))) +
    ggtitle(paste0('Author Nationality Map - ', user)) +
    theme_pander() + theme(plot.title=element_text(hjust=0.5), 
                           legend.position = 'bottom', legend.key.width = unit(1.5, 'cm')) 
  ggsave(paste0('Novelty/goodreads/static/Graphs/', user, '/nationality_map_', user, '.jpeg'), width=12, height=8)
}

export_user_authors <- function(user, list='goodreads_list', authors_db){
  df <- merge(get(list)[[user]], authors_db, by='Author', all.x=T)
  df <- df[,c('Author', 'Title.x', 'gender_fixed', 'nationality1', 'nationality2', 
              'nationality3', 'nationality4', 'Country.Chosen')]
  names(df) <- mapvalues(names(df), from='Title.x', to='Title')
  return (df)
}

create_melted_genre_df <- function(dt) {
  genre_df <- dt[,c('username', grep('^shelf', names(dt), value=T)),with=F]
  genre_df.m <- setDT(melt(genre_df, 
                           id.var='username', value.name = 'Shelf'))
  genre_df.m <- genre_df.m[!Shelf %in% c('Fiction', 'Nonfiction', '')]
  genre_df.m <- genre_df.m[!is.na(Shelf)]
  return (genre_df.m)
}

genre_plot <- function(genre_df, 
                      name, 
                      read_col,
                      n_genre = 10, 
                      n_users = 5,
                      plot=F, 
                      plot_name = 'genre_comparison_',
                      source_col= 'Source',
                      date_col='date_read',
                      random_seed=337,
                      start_year=NA){
  #random_seed
  genre_df.m <- setDT(melt(genre_df, 
                     id.var='Source', value.name = 'Shelf'))

  all_names <- unique(genre_df[,get(source_col)])
  other_names <- sample(setdiff(all_names, name), n_users)
  chosen_names <- c(name, other_names)
  top_table <- genre_df.m[,.(Freq = .N), by = c('Source', 'Shelf')][order(Freq, decreasing = T),]

  ### Calculate average
  genres_total <- setDT(data.frame(table(genre_df.m$Shelf)))
  names(genres_total) <- c('Shelf', 'Freq')
  genres_total$Freq <- genres_total$Freq / nrow(genre_df) * 100
  genres_total$Source <- 'Average'
  top_genres <- unique(top_table[Source %in% chosen_names, .SD[1:n_genre], by=Source]$Shelf)
  genre_plot_df <- top_table[Shelf %in% top_genres & Source %in% chosen_names]
  genre_plot_df <- rbind(genre_plot_df, genres_total[Shelf %in% top_genres])
  genre_plot_df$Source <- mapvalues(genre_plot_df$Source, 
                                    from = other_names,
                                    to = paste0('Reader', 1:length(other_names)))
  # order the shelves based on the order of the user
  genre_plot_df$Shelf <- factor(genre_plot_df$Shelf, 
                            levels = rev(union(unique(genre_plot_df[Source == name]$Shelf),
                                               unique(genre_plot_df$Shelf))))
  ggplot(genre_plot_df) + 
    geom_col(aes(x=Shelf, y=Freq, fill=Source), color='black') +
    facet_grid(. ~ Source, scales='free') + 
    scale_fill_brewer(palette = 'Set1') +
    coord_flip() +
    ggtitle('Genre Plot') +
    theme_pander() + theme(plot.title=element_text(hjust=0.5), 
                           legend.position = 'bottom', legend.key.width = unit(1.5, 'cm')) 
  if (plot==T){
    ggsave(paste0('Novelty/goodreads/static/Graphs/', name, '/', plot_name, name, '.jpeg'), width=14, height=8)
    
  }
}

summary_plot <- function(dt, date_col, 
                         gender_col, narrative_col, 
                         nationality_col, authors_database,
                         name, start_year=1800){
  # plot a 2x2 summary plot of
  # 1. Barplot of genders / fiction
  # 2. Barplot of highest rated books
  # 3. Histogram of publication date
  # 4. Top genres
  source('Novelty/goodreads/scripts/multiplot.R')
  p1 <- gender_bar_plot(dt, gender_col, narrative_col, name)
  p2 <- plot_highest_rated_books(dt)
  p3 <- publication_histogram(dt, date_col)
  p3 <- p3 + ggtitle(paste0('for ', name))
  min_count <- round(nrow(dt)/40)
  p4 <- genre_bar_plot(dt, min_count=min_count)
  jpeg(filename = paste0('Novelty/goodreads/static/Graphs/', name, '/Summary_plot.jpeg'), 
       res = 200, width = 3200, height=2400)
  multiplot(p1, p2, p3, p4, cols=2)
  dev.off()
}

gender_bar_plot <- function(dt, gender_col, narrative_col, name){
  name <- gsub('_', ' ', name)
  dt[[gender_col]] <- mapvalues(dt[[gender_col]],
                                from = c('multiple', 'unknown', 'non-binary'),
                                to = rep('unknown or other', 3),
                                warn_missing = F)
  ggplot(dt) + 
    geom_bar(aes(x=get(narrative_col), fill=get(gender_col)), position=position_dodge()) +
    theme_pander() +
    xlab('') +
    scale_fill_brewer('Gender', palette='Set1') +
    coord_flip() +
    theme(legend.position = 'bottom', plot.title=element_text(hjust=1),
          panel.border = element_rect(colour = "black", fill=NA, size=1)) + 
    ggtitle('Summary Plots')
}

nationality_bar_plot <- function(dt, authors_database, nationality_col='nationality_chosen'){
  dt <- setDT(merge(dt, authors_database, by.x='author', by.y='author_name'))
  dt_sub <- dt[get(nationality_col) != '']
  nation_table_df <- data.frame(table(dt_sub[,get(nationality_col)]))
  names(nation_table_df) <- c('Nationality', 'Count')
  setDT(nation_table_df)
  nation_table_df <- nation_table_df[order(Count)]
  dt_sub$Nationality <-
    factor(dt_sub[,get(nationality_col)], levels = nation_table_df$Nationality)
  ggplot(dt_sub) + geom_bar(aes(x=Nationality), color='black', fill='blue') + 
    coord_flip() + theme_pander() +
    theme(panel.border = element_rect(colour = "black", fill=NA, size=1)) 
}


publication_histogram <- function(dt, date_col, start_year=1800){
  dt_sub <- dt[get(date_col) > start_year]
  n_bins <- max(nrow(dt_sub) / 10, 10)
  ggplot(dt_sub) + geom_histogram(aes(x=get(date_col)), fill='black', bins=n_bins) + 
    theme_pander() +
    xlab('Year of Publication') +
    theme(panel.border = element_rect(colour = "black", fill=NA, size=1)) 
}

genre_bar_plot <- function(dt, n_shelves=4, min_count=2){
  genre_df.m <- create_melted_genre_df(dt)
  genre_df.m <- genre_df.m[variable %in% paste0('shelf', 1:n_shelves)]
  genre_df.m <- genre_df.m[!is.na(Shelf)]
  shelf_table_df <- data.frame(table(genre_df.m$Shelf))
  names(shelf_table_df) <- c('Shelf', 'Count')
  setDT(shelf_table_df)
  shelf_table_df <- shelf_table_df[order(Count)]
  shelf_table_df$Shelf <- factor(shelf_table_df$Shelf, levels = shelf_table_df$Shelf)
  ggplot(shelf_table_df[Count > min_count]) + 
    geom_col(aes(x=Shelf, y=Count), color='black', fill='red') +
    coord_flip() + theme_pander()
}

get_highest_rated_book <- function(dt, rating_col='average_rating', 
                                   title_col='title.simple', author_col='author'){
  most_popular <- dt[which.max(get(rating_col))][, c((author_col), (title_col)), with=F]
  return (paste0(most_popular, collapse = ': '))
}

plot_highest_rated_books <- function(dt, n=10, rating_col='average_rating',
                                     my_rating_col='my_rating',
                                     title_col='title.simple'){
  highest <- tail(dt[order(get(rating_col))], n)
  highest[[title_col]] <- factor(highest[[(title_col)]],
                                     levels = unique(highest[[(title_col)]]))
  highest[[my_rating_col]] <- as.factor(highest[[my_rating_col]])
  ggplot(highest, aes(x=title.simple)) + 
    geom_col(aes(y=get(rating_col), fill=get(my_rating_col))) +
      geom_text(aes(y=get(rating_col)/2, label=get(rating_col))) +
    xlab('Title') + ylab('Average Rating') +
    ylim(0, 5) +
    scale_fill_brewer(palette='Blues', 'Your Rating', type='seq') +
    coord_flip() + theme_pander()
}
