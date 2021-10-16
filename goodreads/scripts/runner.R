require(ggplot2)
require(data.table)
require(ggrepel)
require(forcats)
require(plyr)
require(stringi)
require(rworldmap)
require(RColorBrewer)
require(ggthemes)
setwd('~/Documents/Personal/Repository/Novelty/')
source('goodreads/scripts/utils.R')
args = commandArgs(trailingOnly=TRUE)
file_path <- args[1]
name <- args[2]
library('RPostgres')

#create connection object
con <- RPostgres::dbConnect(drv =Postgres(), 
                            user="cal65", 
                            password=Sys.getenv('cal65_pass'),
                            host="localhost", 
                            port=5432, 
                            dbname="goodreads")
dbListTables(con)
dbGetQuery(con, "SET client_encoding = 'UTF8'")

user <- 'abc'

generate_plots <- function(name){
  query <- paste0("Select * from goodreads_exportdata e left join goodreads_authors as a on e.author = a.author_name where e.username = '", name, "'")
  dt <- setDT(dbGetQuery(con, query))
  dt <- run_all(dt)
  dt$Source <- name
  dir.create(paste0('Graphs/', name), showWarnings = F)
  print(dt)
  # authors_database <- read.csv('goodreads/scripts/authors_database.csv')
  # # update the authors database based on potential new data from dt
  # authors_database <- update_authors_artifact(authors_database, dt)
  # dt$gender <- mapvalues(
  #   dt$Author, 
  #   authors_database$Author, 
  #   authors_database$gender_fixed, warn_missing = F)
  # read plot
  read_plot(dt, name=name, 
            read_col='read', title_col = 'Title.Simple', plot=T)
  # finish plot
  finish_plot(dt, name = name, plot=T)
  # plot world maps
  world_df <- setDT(map_data('world'))
  region_dict <- fread('goodreads/scripts/world_regions_dict.csv')
  region_dict <- region_dict[nationality != '']
  country_dt <- merge_nationalities(dt, authors_database)
  plot_map_data(country_dt, region_dict=region_dict, world_df=world_df, user=name)
  # cannot do genre plot with just an individual's data. To figure out better path
  # month plot
  # month_plot(dt, name=name, date_col='Date.Read', 
  #            page_col='Number.of.Pages', title_col='Title.Simple',
  #            author_gender_col='gender', lims=c(2010, 2022), save=T)
  # # year plot
  year_plot(dt, name=name, fiction_col='Narrative', 
            date_col='Date.Read', page_col='Number.of.Pages', 
            title_col='Title.Simple', author_gender_col='gender', save=T)
  # # summary plot
  summary_plot(dt, date_col='Original.Publication.Year', gender_col = 'gender', 
               narrative_col='Narrative', nationality_col='Country.Chosen', 
               authors_database = authors_database, name = name)
}
generate_plots(name)