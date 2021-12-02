require(ggplot2)
require(data.table)
require(forcats)
require(plyr)
require(stringi)
library(rnaturalearth) # for map data
require(RColorBrewer)
require(ggthemes)
setwd(Sys.getenv('repo'))
source('Novelty/goodreads/scripts/utils.R')
args = commandArgs(trailingOnly=TRUE)
name <- args[1]
library('RPostgres')

#create connection object
con <- RPostgres::dbConnect(drv =Postgres(), 
                            user="cal65", 
                            password=Sys.getenv('cal65_pass'),
                            host="localhost", 
                            port=5432, 
                            dbname="goodreads")
#dbListTables(con)
#dbGetQuery(con, "SET client_encoding = 'UTF8'")


generate_plots <- function(name){
  query <- paste0("Select * from goodreads_exportdata e left join goodreads_authors as a 
                           on e.author = a.author_name where e.username = '", name, "'")
  dt <- setDT(dbGetQuery(con, query))
  dt <- run_all(dt)
  dt$source <- name
  print(head(dt))
  dir.create(paste0('Novelty/goodreads/static/Graphs/', name), showWarnings = F)
  # # update the authors database based on potential new data from dt
  # authors_database <- update_authors_artifact(authors_database, dt)
  # dt$gender <- mapvalues(
  #   dt$Author, 
  #   authors_database$Author, 
  #   authors_database$gender_fixed, warn_missing = F)
  # read plot
  read_plot(dt, name=name, 
            read_col='read', title_col = 'title_simple', plot=T)
  # finish plot
  finish_plot(dt, name = name, plot=T)
  # plot world maps
  world_df <- setDT(map_data('world'))
  region_dict <- fread('Novelty/goodreads/scripts/world_regions_dict.csv')
  region_dict <- region_dict[nationality != '']
  authorQuery <- "Select * from goodreads_authors"
  authors_database <- setDT(dbGetQuery(con, authorQuery))
  print(head(authors_database))
  plot_map_data(dt, region_dict=region_dict, world_df=world_df, user=name)
  # cannot do genre plot with just an individual's data. To figure out better path
  # month plot
  if (length(unique(dt$date.read) > 2)){
    month_plot(dt, name=name, date_col='date_read', 
               page_col='number_of_pages', title_col='title_simple',
               author_gender_col='gender', lims=c(2010, 2022), save=T)
  }

  # # year plot
  year_plot(dt, name=name, fiction_col='Narrative', 
            date_col='date_read', page_col='number_of_pages', 
            title_col='title_simple', author_gender_col='gender', save=T)
  # # summary plot
  summary_plot(dt, date_col='original_publication_year', gender_col = 'gender', 
               narrative_col='Narrative', nationality_col='nationality_chosen', 
               authors_database = authors_database, name = name)
}

# create folder in static
dir.create(file.path('Novelty/goodreads/static/Graphs', name), showWarnings = FALSE)
generate_plots(name)