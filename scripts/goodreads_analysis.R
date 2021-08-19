library(data.table)
library(ggplot2)
library(stringr)
library(scales)
library(ggrepel)
library(ggthemes)
library(rworldmap)
library(rnaturalearth) # for map data

setwd('~/Documents/CAL/Real_Life/Repository/Books/')
source('utils.R')

file_start <- 'data/goodreads_library_export_'
paths <- list('Cal' = paste0(file_start, 'cal_appended.csv'), 
              'Andrea' = paste0(file_start, 'andrea_appended.csv'),
              'Glen'  = 'data/goodreads_library_export_glen_appended.csv',
              'Sarah' = 'data/goodreads_library_export_sarahgrey_appended.csv',
              'Adam' = 'data/goodreads_library_export_adam_appended.csv',
              'Ruby' = paste0(file_start, 'ruby_appended.csv'),
              'Liz' = paste0(file_start, 'liz_appended.csv'),
              'Charlotte' = paste0(file_start, 'charlotte_appended.csv'),
              'Corinne' = paste0(file_start, 'corinne_appended.csv'),
              'Sarah_McNabb' = paste0(file_start, 'sarahmcnabb_appended.csv'),
              'Bernadette' = paste0(file_start, 'bernadette_appended.csv'),
              'Elena' = paste0(file_start, 'elena_appended.csv'),
              'Bev' = paste0(file_start, 'bev_appended.csv'),
              'Mery' = paste0(file_start, 'mery_appended.csv'),
              'Viki' = paste0(file_start, 'viki_appended.csv'),
              'Marian' = paste0(file_start, 'marian_appended.csv'),
              'Maggie' = paste0(file_start, 'maggie_appended.csv'),
              'Luisa' = paste0(file_start, 'luisa_appended.csv'),
              'Ben_Goldsmith' = paste0(file_start, 'ben_goldsmith_appended.csv'),
              'Josh_Z' = paste0(file_start, 'josh_z_appended.csv'),
              'Maryann' = paste0(file_start, 'maryann_appended.csv'),
              'Stephanie' = 'data/goodreads_library_SHopkins_appended.csv',
              'Tiff' = paste0(file_start, 'tiff_appended.csv'))
goodreads_list <- lapply(paths, run_all)
for (name in names(paths)){
  goodreads_list[[name]]$Source <- name
  dir.create(paste0('Graphs/', name), showWarnings = F)
}
authors_database <- read.csv('authors_database.csv')
for (name in names(paths)){
  goodreads_list[[name]][!gender %in% c('female', 'male')]$gender <- mapvalues(
    goodreads_list[[name]][!gender %in% c('female', 'male')]$Author, 
    authors_database$Author, 
    authors_database$gender_fixed, warn_missing = F)
  missing_data <- goodreads_list[[name]][!Author %in% authors_database$Author][, c('Author', 'Title', 'gender')]
  missing_data <- missing_data[, .(Title = head(Title,1)), by=c('Author', 'gender')]
  if (nrow(missing_data) > 0){
    names(missing_data) <- mapvalues(names(missing_data),
                                       from = 'gender', to = 'gender_guessed')
    print(nrow(missing_data))
    missing_data$country_chosen <- NA
    missing_data$gender_fixed <- ifelse(missing_data$gender_guessed %in% c('male', 'female'), missing_data$gender_guessed, NA)
    write.csv(missing_data, 'new_authors_data.csv', row.names=F)
    system('/Users/christopherlee/anaconda3/bin/python3 google_answer.py new_authors_data.csv')
    system('/Users/christopherlee/anaconda3/bin/python3 choose_nationality.py new_authors_data.csv')
    system('/Users/christopherlee/anaconda3/bin/python3 wikipedia.py new_authors_data.csv')
    missing_data <- read.csv('new_authors_data.csv')
    authors_database <- rbind.fill(authors_database, missing_data)
    # because of the multiple programming languages, have this awkward write python read pipeline
    write.csv(authors_database, 'authors_database.csv', row.names=F)
    authors_database$gender_fixed <- ifelse(authors_database$gender_fixed=='', 
                                                authors_database$gender_guessed,
                                                authors_database$gender_fixed)
    goodreads_list[[name]][!gender %in% c('female', 'male')]$gender <- mapvalues(
      goodreads_list[[name]][!gender %in% c('female', 'male')]$Author, 
      authors_database$Author, 
      authors_database$gender_fixed, warn_missing = F)
    write.csv(goodreads_list[[name]], paths[[name]], row.names=F)
    }
  rm(missing_data)
}
books_combined <- setDT(do.call('rbind.fill', goodreads_list))

for (name in names(paths)){
  read_plot(goodreads_list[[name]][Read.Count>0], name=name, 
            read_col='Read', title_col = 'Title.Simple', plot=T)
  finish_plot(goodreads_list[[name]], name = name, plot=T)
  year_comparison(goodreads_list, 
                  year_col='Original.Publication.Year', 
                  year_start=1780,
                  user = name, plot=T)
  yearly_gender_graph(goodreads_list[[name]], name=name, gender_col='gender', 
                      date_col='Date.Read', save=T)
}

# plot world maps
world_sf <- ne_countries(returnclass = "sf", scale = "large", type='map_units')
region_dict <- fread('world_regions_dict.csv')
region_dict <- region_dict[nationality != '']
authors_database <- read.csv('authors_database.csv')
country_dict = vector('list')
for (name in names(paths)){
  country_dict[[name]] <- merge_nationalities(goodreads_list[[name]], authors_database)
  plot_map_data(country_dict[[name]][Exclusive.Shelf =='read'], 
                region_dict=region_dict, world_sf=world_sf, 
                user=name)
}

lapply(country_dict, function(x) length(which(is.na(x$Country.Chosen) | x$Country.Chosen=='')))
unique(authors_database[which(!authors_database$Country.Chosen %in% region_dict$nationality),]$Country.Chosen)

# genre plotting
genre_df <- books_combined[Exclusive.Shelf == 'read']
genre_df <- books_combined[Date.Read > '2010-01-01' | is.na(Date.Read),
                           c('Source', grep('^Shelf', names(books_combined), value=T)),with=F]
genre_df.m <- create_melted_genre_df(genre_df)
for (name in names(paths)){
  genre_plot(genre_df, name = name, n_genre = 24, read_col='Read',  plot=T)
}



## Month plot
for (name in names(paths)){
  month_plot(goodreads_list[[name]], name=name, date_col='Date.Read', 
           page_col='Number.of.Pages', title_col='Title.Simple',
           author_gender_col='gender', lims=c(2010, 2022), save=T)
  year_plot(goodreads_list[[name]], name=name, fiction_col='narrative', 
            date_col='Date.Read', page_col='Number.of.Pages', 
            title_col='Title.Simple', author_gender_col='gender', save=T)

}
 
# gender analysis by unique authors
unique_authors <- unique(books_combined[,c('Author', 'gender', 'Source')])
gender_count <- unique_authors[, .(male=sum(gender=='male', na.rm=T), 
                                   female=sum(gender=='female', na.rm=T), total=.N), by='Source']
gender_count$ratio <- with(gender_count, male/total)
gender_count$unknown <- with(gender_count, total - (male + female))
gender_count.m <- melt(gender_count[,c('Source', 'male', 'female', 'unknown')], id = 'Source',
                       value.name = 'count', variable.name='gender')
ggplot(gender_count.m) +
  geom_col(aes(x=Source, y=count, fill=gender), position = position_dodge()) +
  scale_fill_brewer(palette = 'Dark2') + 
  coord_flip() + ylab('Number of Authors') +
  ggtitle('Gender Breakdown by User') + 
  theme_pander() + theme(plot.title=element_text(hjust=0.5))
ggsave('Graphs/Gender_breakdown_users.jpeg', width=10, height=7)

for (name in names(goodreads_list)){
  rating_gender <- goodreads_list[[name]][,c('Author', 'Narrative', 'gender', 'My.Rating')]
  rating_count <- rating_gender[, .(Rating.Count = .N), by =c('Narrative', 'My.Rating')]
  rating_gender <- merge(rating_gender, rating_count, by = c('Narrative', 'My.Rating'))
  rating_gender$text_size <- pmin(10, 100/rating_gender$Rating.Count)
  ggplot(rating_gender) +
    geom_tile(aes(x=Narrative, y=Author, fill=gender), color='black') +
    scale_fill_brewer(palette = 'Dark2') +
    geom_text(aes(x=Narrative, y=Author, label=Author, size=text_size)) +
    scale_size_continuous(guide=F) +
    facet_wrap(Narrative ~ My.Rating, scales='free', nrow=2) +
    theme(axis.text.y = element_blank(),
          plot.title = element_text(hjust=0.5),
          panel.background = element_blank())
  ggsave(paste0('Graphs/', name, '/gender_ratings_', name, '.jpeg'), width=15, height=9, dpi=180)
}

for (name in names(goodreads_list)){
  summary_plot(goodreads_list[[name]], date_col='Original.Publication.Year', gender_col = 'gender', 
               narrative_col='Narrative', nationality_col='Country.Chosen', 
               authors_database = authors_database, name = name)
}

## top 100
for (name in names(goodreads_list)){
  graph_list(goodreads_list[[name]], 'artifacts/100_books_to_read.csv', '100_Books_to_Read_in_Your_Lifetime', save=T)
  graph_list(goodreads_list[[name]], 'artifacts/100_best_memoirs.csv', '100_Best_Memoirs', save=T)
}
