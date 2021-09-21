options(stringsAsFactors = F)
library(ggplot2)
library(data.table)
library(ggrepel)
library(forcats)
library(plyr)
library(stringi)
library(RColorBrewer)
setwd('~/Documents/CAL/Real_Life/Repository/Books/')

preprocess <- function(dt){
  dt$gender <- mapvalues(dt$gender,
                                       from = c('mostly_male', 'mostly_female'),
                                       to = c('male', 'female'), warn_missing = FALSE)
  names(dt) <- gsub(' ', '.', names(dt))
  dt$Date.Read <- as.Date(dt$Date.Read, format = '%Y-%m-%d')
  dt$Title.Simple <- gsub(':.*', '', dt$Title)
  dt$Title.Simple <- gsub('\\(.*\\)', '', dt$Title.Simple)
  dt$Exclusive.Shelf <- mapvalues(dt$Exclusive.Shelf,
                                  from = c('2020-books', 'currently-reading', 'to-read'),
                                  to=c('unread', 'unread', 'unread'), warn_missing = FALSE)
  
  return(dt)
}

narrative <- function(dt){
  dt$Narrative <- apply(
    dt, 1, function(x) ifelse(any(
    grepl('Nonfiction|Memoir', x[c('Shelf1', 'Shelf2', 'Shelf3', 'Shelf4')])
    ), 'Nonfiction', 'Fiction')
  )
  return(dt)
}

read_percentage <- function(dt){
  # It seems sometimes the "added by" value is off by a factor of 10. When the 
  # number of people listing the book as "to read" is larger than total added by, multiply by 10
  dt[To_reads > Added_by, Added_by := Added_by * 10] 
  dt$Read <- with(dt, Added_by - To_reads)
  dt$Read.Percentage <- with(dt, Read / Added_by)
  
  return(dt)
}

run_all <- function(csv_path){
  dt <- fread(csv_path)
  dt <- preprocess(dt)
  dt <- narrative(dt)
  dt <- read_percentage(dt)
  return(dt)
}

preprocess_dt <- function(dt){
  dt <- dt[Title != '']
  dt$Added_by[is.na(dt$Added_by)] <- 0
  dt$To_reads[is.na(dt$To_reads)] <- 0
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
  df$Year.Read <- as.numeric(format(df[[date_col]], '%Y'))
  df$Month.Read  <- as.numeric(format(df[[date_col]], '%m'))
  if (length(unique(df$Year.Read)) < 1) {
    return()
  }
  df <- df[!is.na(Year.Read)]
  if (!is.null(lims)){
    df <- df[Year.Read > lims[1] & Year.Read < lims[2]]
  }
  ggplot(df, 
         aes(x=Month.Read, y=get(page_col), group=fct_rev(fct_inorder(get(title_col))))) + 
    geom_col(aes(fill=get(author_gender_col)), width=1, alpha=0.65, color='black') + 
    facet_grid(Year.Read ~ .) +
    scale_fill_brewer('Author Gender', palette = 'Pastel1', guide=F) +
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
    ggsave(paste0('Graphs/', name, '/Monthly_pages_read_', name, '.jpeg'), width=15, height=9, dpi=180)
  }
}

year_plot <- function(df, name, fiction_col, date_col, page_col, 
                      title_col, author_gender_col, str_len=30, start_year = 2010,
                      save=F){
  divergent_df <- df
  divergent_df$Pages <- with(divergent_df, ifelse(get(fiction_col) == 'Fiction', -1*get(page_col), get(page_col)))
  str_len <- str_len
  divergent_df$Year.Read <- format(divergent_df[[date_col]], '%Y')
  # exit function if there is no date data
  if (length(unique(divergent_df$Year.Read)) < 1) {
    return()
  }
  divergent_df[[title_col]] <- sapply(divergent_df[[title_col]],
                               function(x) paste(stri_wrap(x, width=str_len), collapse='\n'))
  ggplot(divergent_df[Year.Read >= start_year], aes(x=Year.Read, y=Pages, group=fct_rev(fct_inorder(get(title_col))))) +
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
    ggsave(paste0('Graphs/',  name, '/Yearly_pages_read_', name, '.jpeg'), width=15, height=9)
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
                      date_col='Date.Read',
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
  # order title text by popularity
  df <- df[order(get(read_col))]
  df[[title_col]] <- factor(df[[title_col]], levels = unique(df[[title_col]]))
  labels = generate_labels(prettyNum(breaks, big.mark = ',', scientific=F))
  df$strats <- cut(df[[read_col]], breaks = breaks, 
                   labels = labels)
  # 1 text size for each strat
  text_sizes <- df[, .(text_size = 120/max(title_length)), by = strats]
  df <- merge(df, text_sizes, by='strats', all.x=T)
  
  ggplot(df, aes(x=strats, y=get(title_col))) +
    geom_tile(aes(fill=Narrative), color='black') +
    geom_text(aes(label = get(title_col), size = text_size)) +
    facet_wrap(strats ~ ., scales='free', nrow=1) +
    scale_fill_manual(values = c('hotpink2', 'darkolivegreen')) +
    scale_size_continuous(guide=F, range=c(2, 5)) +
    xlab('Number of Readers') + 
    ylab('Title') +
    ggtitle(paste0('Readership Spectrum - ', name)) +
    theme(axis.text.y = element_blank(),
          plot.title = element_text(hjust=0.5),
          panel.background = element_blank())
  if (plot){
    ggsave(paste0('Graphs/', name, '/', plot_name, name, '.jpeg'), width = 16, height=9, dpi=100)
  }
}

### % finish plot
finish_plot <- function(df, 
                      name, 
                      read_col = 'Read.Percentage',
                      exclusive_shelf = 'Exclusive.Shelf',
                      n = 10, 
                      plot=F, 
                      plot_name = 'finish_plot_'){
  df_read <- df[order(get(read_col)),]
  df_read <- df_read[!is.na(get(read_col))]
  # keep only bottom n
  df_read_n <- df_read[, head(.SD, n), by=get(exclusive_shelf)]
  df_read_n$Title.Simple <- factor(df_read_n$Title.Simple,
                                 levels = unique(df_read_n$Title.Simple))
  ggplot(df_read_n, aes(x=Title.Simple)) +
    geom_col(aes( y=1), fill='Dark Blue') +
       geom_col(aes( y=get(read_col)), fill='red') +
    geom_text(aes(y=get(read_col)/2, label = paste0(Read, ' / ', Added_by)), 
              size=n * 3/5, color='white', hjust=0) +
    facet_grid(get(exclusive_shelf) ~ ., scales='free', space='free') +
    ylim(0, 1) +
    xlab('Title') +
    ylab('Reading Percentage') +
       coord_flip() + 
       ggtitle('Least Finished Reads') +
       theme_pander() +
       theme(plot.title = element_text(hjust=0.5))
  if (plot == T){
    ggsave(paste0('Graphs/', name, '/', plot_name, name, '.jpeg'), width=12, height=8)
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
    ggsave(paste0('Graphs/', user, '/publication_year_', user, '.jpeg'), width=12, height=8)
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
  write.csv(authors_new, 'new_authors_data.csv', row.names=F)
  system('/Users/christopherlee/anaconda3/bin/python3 google_answer.py new_authors_data.csv')
  system('/Users/christopherlee/anaconda3/bin/python3 choose_nationality.py new_authors_data.csv')
  system('/Users/christopherlee/anaconda3/bin/python3 wikipedia.py new_authors_data.csv')
  new_data <- read.csv('new_authors_data.csv')
  artifact <- rbind.fill(artifact, new_data)
  # because of the multiple programming languages, have this awkward write python read pipeline
  write.csv(artifact, 'authors_database.csv', row.names=F)
  return (artifact)
}

merge_nationalities <- function(df, authors_db, country_col = 'Country.Chosen'){
  df <- merge(df, authors_db[,c('Author', country_col)], by='Author', all.x=T)
  return (df)
}

plot_map_data <- function(df, region_dict, world_sf, user, country_col = 'Country.Chosen'){
  # defining other df for subregions not included in the world simple features
  # choosing to define here because it's low cost and multiple lines of code. 
  # Including Hong Kong and the countries of the United Kingdom
  hk_sf <- ne_states(geounit = "Hong Kong S.A.R.", returnclass = "sf")
  uk_sf <- ne_states(country = "united kingdom", returnclass = "sf")
  other_sf <- rbind(uk_sf, hk_sf)
  names(other_sf) <- mapvalues(names(other_sf), from = 'geonunit', to='geounit')
  
  country_df <- merge(df, region_dict, by.x='Country.Chosen', by.y='nationality', all.x=T)
  regions_count <- country_df[, .(count = .N, titles = paste(head(Title.Simple, 3), collapse='\n')), by=region]
  world_sf <- merge(world_sf, 
                    regions_count, by.x='geounit', by.y='region', all.x=T)
  
  other_sf <- merge(other_sf, regions_count, by.x='geounit', by.y='region', all.x=T)
  max_count = max(regions_count$count)
  my_breaks <- c(1, rep(2^(1:round(log2(max_count)))))
  ggplot(world_sf) + 
    geom_sf(aes(fill=count, group=geounit, text=titles), size=0.1) +
    geom_sf(data=other_sf, aes(fill=count, group=geounit), color=NA) +
    scale_fill_gradientn(name = "count", trans = "log", breaks=my_breaks,
                        colors=brewer.pal(9, 'YlOrRd')) +
    ggtitle(paste0('Author Nationality Map - ', user)) +
    theme_pander() + theme(plot.title=element_text(hjust=0.5), 
                           legend.position = 'bottom', legend.key.width = unit(1.5, 'cm')) 
  ggsave(paste0('Graphs/', user, '/nationality_map_', user, '.pdf'), width=12, height=8)
  #world_plotly <- ggplotly(tool_tip=c('geounit', 'count', 'titles'), original_data=F)
  #htmlwidgets::saveWidget(world_plotly, paste0('Graphs/', user, '/nationality_map_', user, '.html'))
}

export_user_authors <- function(user, list='goodreads_list', authors_db){
  df <- merge(get(list)[[user]], authors_db, by='Author', all.x=T)
  df <- df[,c('Author', 'Title.x', 'gender_fixed', 'nationality1', 'nationality2', 
              'nationality3', 'nationality4', 'Country.Chosen')]
  names(df) <- mapvalues(names(df), from='Title.x', to='Title')
  return (df)
}

create_genre_df <- function(dt) {
  ## grab all the columns starting with Shelf, as well as Source
  genre_df <- dt[,c('Source', grep('^Shelf', names(dt), value=T)),with=F]
  return (genre_df)
}

create_melted_genre_df <- function(dt, additional_exclude=c('Audiobook')) {
  genre_df <- dt[,c('Source', grep('^Shelf', names(dt), value=T)),with=F]
  genre_df.m <- setDT(melt(genre_df, 
                           id.var='Source', value.name = 'Shelf'))
  genre_df.m <- genre_df.m[!Shelf %in% c('Fiction', 'Nonfiction', '', additional_exclude)]
  genre_df.m <- genre_df.m[!is.na(Shelf)]
  return (genre_df.m)
}

create_genre_difference_df <- function(genre_df){
  melted_genre_df <- create_melted_genre_df(genre_df)
  top_table <- melted_genre_df[,.(Freq = .N), 
                          by = c('Source', 'Shelf')][order(Freq, decreasing = T),]
  # I want to make a table with all sources and shelves
  all_genres <- unique(melted_genre_df$Shelf)
  all_table <- data.frame(Source=rep(unique(genre_df$Source), each = length(all_genres)),
                          Shelf = rep(all_genres, length(unique(genre_df$Source))))
  all_table <- merge(all_table, top_table, by = c('Source', 'Shelf'), all.x=T)
  all_table$Freq[is.na(all_table$Freq)] <- 0
  setDT(all_table)
  all_table <- all_table[order(Freq)]
  ### Calculate average frequencies of genres
  genres_total <- setDT(data.frame(table(melted_genre_df$Shelf)))
  names(genres_total) <- c('Shelf', 'Freq')
  genres_total$Ratio_Total <- genres_total$Freq / nrow(genre_df) * 100
  genres_total$Source <- 'Average'
  ## To do, calculate user averages and merge with this total table, calculate difference
  ## Use greatest and highest differences as top and bottom genres
  n_source <- genre_df[, .N, by=Source]
  all_table <- merge(all_table, n_source)
  all_table$Ratio <- with(all_table, Freq / N * 100)
  # for each user, calculate their genre ratio and compare to average
  genre_table_merged <- merge(all_table, genres_total[,c('Shelf', 'Ratio_Total')], by='Shelf')
  genre_table_merged$Diff <- with(genre_table_merged, sqrt(Ratio) - sqrt(Ratio_Total))
  setDT(genre_table_merged)
  # return dataframe from least read to most read genres for all users
  genre_table_merged <- genre_table_merged[order(Diff)]
  
  return(list('genres_total' = genres_total, 'genre_table_merged' = genre_table_merged))
}

genre_plot <- function(genre_df, 
                      name, 
                      read_col,
                      n_genre = 20, 
                      plot=F, 
                      plot_name = 'genre_comparison_',
                      source_col= 'Source',
                      date_col='Date.Read',
                      random_seed=337,
                      start_year=NA){
  #random_seed
  genre_df.m <- create_melted_genre_df(setDT(genre_df))
  # get dataframe 
  genre_list <- create_genre_difference_df(genre_df)
  genres_total <- genre_list$genres_total
  genre_table_merged <- genre_list$genre_table_merged
  user_table <- genre_table_merged[Source == name]
  top_genres <-  tail(user_table$Shelf, n_genre)
  bottom_genres <- head(user_table$Shelf, n_genre)
  
  # plot only shelves in top and bottom
  genre_plot_df <- user_table[Shelf %in% c(top_genres, bottom_genres)]
  genres_select <- genres_total[Shelf %in% c(bottom_genres, top_genres)]
  names(genres_select) <- mapvalues(names(genres_select), from = 'Ratio_Total',
                                    to = 'Ratio')
  genre_plot_df <- setDT(rbind.fill(genre_plot_df, genres_select))

  # order the shelves based on the order of the user
  genre_plot_df$Shelf <- factor(genre_plot_df$Shelf, 
                            levels = rev(union(unique(genre_plot_df[Source == name]$Shelf),
                                               unique(genre_plot_df$Shelf))))
  genre_plot_df$Type <- ifelse(genre_plot_df$Shelf %in% top_genres, 'Above Average', 'Below Average')
  ggplot(genre_plot_df) + 
    geom_col(aes(x=Shelf, y=Ratio, fill=Source), color='black', position=position_dodge()) +
    facet_wrap(. ~ Type, scales='free') + 
    scale_fill_brewer(palette = 'Set1') +
    coord_flip() +
    ggtitle(paste0('Genre Comparison Plot - ', name)) +
    theme_pander() + 
    theme(plot.title=element_text(hjust=0.5), 
                           legend.position = 'bottom', legend.key.width = unit(1.5, 'cm'),
          panel.border = element_rect(color='black', fill=NA)) 
  if (plot==T){
    ggsave(paste0('Graphs/', name, '/', plot_name, name, '.jpeg'), width=14, height=8)
    
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
  source('multiplot.R')
  p1 <- gender_bar_plot(dt, gender_col, narrative_col, name) 
  # p2 <- nationality_bar_plot(dt, authors_database, nationality_col)
  p2 <- plot_longest_books(dt) + ggtitle('Longest Books')
  p3 <- publication_histogram(dt, date_col) + ggtitle('Publication Years')
  p3 <- p3 + ggtitle(paste0('for ', name))
  min_count <- round(nrow(dt)/40)
  p4 <- genre_bar_plot(dt, min_count=min_count) + ggtitle('Most Common Genres')
  jpeg(filename = paste0('Graphs/', name, '/Summary_plot.jpeg'), 
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
    # preserve parameter allows for equal bar heights
    geom_bar(aes(x=get(narrative_col), fill=get(gender_col)), 
             position=position_dodge2(preserve = 'single')) +
    theme_pander() +
    xlab('') + ylab('Count') +
    scale_fill_brewer('Gender', palette='Set1') +
    coord_flip() +
    theme(legend.position = 'bottom', plot.title=element_text(hjust=1),
          axis.text = element_text(size=12),
          plot.background = element_rect(colour = "black", fill=NA, size=0.5)) + 
    ggtitle('Summary Plots')
}

nationality_bar_plot <- function(dt, authors_database, name,
                                 nationality_col='Country.Chosen', save=F){
  dt <- setDT(merge(dt, authors_database, by='Author'))
  dt_sub <- dt[get(nationality_col) != '']
  nation_table_df <- data.frame(table(dt_sub[,get(nationality_col)]))
  names(nation_table_df) <- c('Nationality', 'Count')
  setDT(nation_table_df)
  nation_table_df <- nation_table_df[order(Count)]
  dt_sub$Nationality <-
    factor(dt_sub[,get(nationality_col)], levels = nation_table_df$Nationality)
  ggplot(dt_sub) + geom_bar(aes(x=Nationality), color='black', fill='blue') + 
    coord_flip() + theme_pander() +
    theme(plot.background = element_rect(colour = "black", fill=NA, size=0.5)) 
  if (save == T){
    ggsave(paste0('Graphs/', name, '/nationality_barplot_' , name, '.jpeg'), width=11, height=8)
  }
}


publication_histogram <- function(dt, date_col, start_year=1800){
  dt_sub <- dt[get(date_col) > start_year]
  n_bins <- max(3*sqrt(nrow(dt_sub)), 50)
  ggplot(dt_sub) + geom_histogram(aes(x=get(date_col)), fill='black', bins=n_bins) + 
    theme_pander() +
    xlab('Year of Publication') + ylab('Count') +
    theme(plot.background = element_rect(colour = "black", fill=NA, size=0.5),
          axis.title.y = element_text(vjust=-2)) 
}

genre_bar_plot <- function(dt, n_shelves=4, min_count=2){
  genre_df.m <- create_melted_genre_df(dt)
  genre_df.m <- genre_df.m[variable %in% paste0('Shelf', 1:n_shelves)]
  genre_df.m <- genre_df.m[!is.na(Shelf)]
  shelf_table_df <- data.frame(table(genre_df.m$Shelf))
  names(shelf_table_df) <- c('Shelf', 'Count')
  setDT(shelf_table_df)
  shelf_table_df <- shelf_table_df[order(Count)]
  shelf_table_df$Shelf <- factor(shelf_table_df$Shelf, levels = shelf_table_df$Shelf)
  ggplot(shelf_table_df[Count > min_count]) + 
    geom_col(aes(x=Shelf, y=Count), color='black', fill='red') +
    coord_flip() + theme_pander() + ylab('') +
    theme(plot.background = element_rect(colour = "black", fill=NA, size=0.5))
}

get_highest_rated_book <- function(dt, rating_col='Average.Rating', 
                                   title_col='Title.Simple', author_col='Author'){
  most_popular <- dt[which.max(get(rating_col))][, c((author_col), (title_col)), with=F]
  return (paste0(most_popular, collapse = ': '))
}

plot_highest_rated_books <- function(dt, n=10, rating_col='Average.Rating',
                                     my_rating_col='My.Rating',
                                     title_col='Title.Simple'){
  highest <- tail(dt[order(get(rating_col))], n)
  highest[[title_col]] <- factor(highest[[(title_col)]],
                                     levels = unique(highest[[(title_col)]]))
  highest[[my_rating_col]] <- as.factor(highest[[my_rating_col]])
  ggplot(highest, aes(x=Title.Simple)) + 
    geom_col(aes(y=get(rating_col), fill=get(my_rating_col))) +
      geom_text(aes(y=get(rating_col)/2, label=get(rating_col))) +
    xlab('Title') + ylab('Average Rating') +
    ylim(0, 5) +
    scale_fill_brewer(palette='Blues', 'Your Rating', type='seq') +
    coord_flip() + theme_pander()
}

plot_longest_books <- function(dt, n=10, pages_col='Number.of.Pages', 
                               title_col='Title.Simple',
                               my_rating_col='My.Rating'){
  
  highest <- tail(dt[!is.na(get(pages_col))][order(get(pages_col))], n)
  highest[[title_col]] <- factor(highest[[(title_col)]],
                                 levels = unique(highest[[(title_col)]]))
  highest[[my_rating_col]] <- as.factor(highest[[my_rating_col]])
  ggplot(highest, aes(x=Title.Simple)) + 
    geom_col(aes(y=get(pages_col), fill=get(my_rating_col))) +
    geom_text(aes(y=get(pages_col)/2, label=get(pages_col))) +
    xlab('') + ylab('Number of Pages') +
    scale_fill_brewer(palette='Blues', 'Your Rating', type='seq') +
    coord_flip() + theme_pander() +
    theme(plot.background = element_rect(colour = "black", fill=NA, size=0.5))
}

yearly_gender_graph <- function(dt, name, date_col, gender_col, year_start=NA,
                                plot_name="gender_breakdown_by_year_", save=F){
  dt$Year.Read <- as.numeric(format(dt[[date_col]], '%Y'))
  if (length(unique(dt$Year.Read)) < 2) {
    print("Not enough years to graph")
    return()
  }
  if (!is.na(year_start)){
    dt <- dt[Year.Read >= year_start]
  }
  min_year = min(dt$Year.Read, na.rm=T)
  max_year = max(dt$Year.Read, na.rm=T)
  ggplot(dt) + 
    geom_bar(aes(x=get(gender_col), fill=get(gender_col)), 
                              position = position_dodge2(0.7, preserve = 'single')) +
    scale_fill_brewer(palette='Set1', 'Author Gender') +
    facet_grid(. ~ Year.Read) +
    theme_pander() + xlab('') +
    ggtitle('Gender Breakdown by Year') +
    theme(axis.text.x=element_blank(), axis.title.x = element_blank(), 
          panel.border=element_rect(colour="black",size=1),
          plot.title = element_text(hjust=0.5))
  if (save==T){
    print("Saving yearly gender breakdown plot")
    ggsave(paste0('Graphs/', name, '/', plot_name, name, '.jpeg'), width=14, height=8)
  }
}

graph_list <- function(dt, list_name, plot_name, save=F){
  top_list_df <- fread(list_name)
  # merging just by Book.Id may miss near matches with similar titles
  # for now, check if titles are the same and change the book.id
  top_list_df$Title.Upper <- toupper(top_list_df$Title)
  
  dt$Title.Upper <- toupper(dt$Title.Simple)
  dt$Match <- dt$Book.Id %in% top_list_df$Book.Id
  unmatched_titles <- dt[Match==F & Title.Upper %in% top_list_df$Title.Upper]$Title.Upper
  for (title in unmatched_titles){
    dt[Title.Upper==title]$Book.Id <- top_list_df[Title.Upper == title]$Book.Id
  }
  top_books <- merge(top_list_df, dt[,c('Book.Id', 'Source', 'gender', 'Date.Read')], 
                     by='Book.Id', all.x=T)
  setDT(top_books)
  top_books$Read <- ifelse(is.na(top_books$Source), F, T)
  top_books$Year.Read <- format(top_books$Date.Read, '%Y')
  palette <- c('grey40', 'Purple')
  plot_title <- gsub('_', ' ', plot_name)
  ggplot(top_books, aes(x=1, y=Title)) +
    geom_tile(aes(fill=Read), color='black') +
    geom_text(aes(label=Year.Read)) +
    facet_wrap(Facet ~ ., scales='free') +
    scale_fill_manual(values = palette) +
    ggtitle(paste0(plot_title, ' - ', name)) +
    theme_pander() +
    theme(axis.text.x = element_blank(), plot.title=element_text(hjust=0.5),
          axis.title.x = element_blank())
  if (save == T){
    ggsave(paste0('Graphs/', name, '/', plot_name, '_', name, '.jpeg'), width=9.5, height=7)
  }
}
