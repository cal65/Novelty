require(ggplot2)
require(data.table)
require(ggrepel)
require(forcats)
require(plyr)
require(stringi)
require(rworldmap)
require(RColorBrewer)
require(ggthemes)
source('goodreads/scripts/utils.R')
args = commandArgs(trailingOnly=TRUE)
file_path <- args[1]
name <- args[2]

generate_plots <- function(file_path, name){
  dt <- run_all(file_path)
  dt$Source <- name
  dir.create(paste0('Graphs/', name), showWarnings = F)
  authors_database <- read.csv('goodreads/scripts/authors_database.csv')
  # update the authors database based on potential new data from dt
  authors_database <- update_authors_artifact(authors_database, dt)
  dt$gender <- mapvalues(
    dt$Author, 
    authors_database$Author, 
    authors_database$gender_fixed, warn_missing = F)
  dt_read <- dt[Exclusive.Shelf == 'read']
  # read plot
  read_plot(dt_read, name=name, 
            read_col='Read', title_col = 'Title.Simple', plot=T)
  # finish plot
  finish_plot(dt_read, name = name, plot=T)
  # plot world maps
  world_df <- setDT(map_data('world'))
  region_dict <- fread('goodreads/scripts/world_regions_dict.csv')
  region_dict <- region_dict[nationality != '']
  country_dt <- merge_nationalities(dt_read, authors_database)
  plot_map_data(country_dt, region_dict=region_dict, world_df=world_df, user=name)
  # cannot do genre plot with just an individual's data. To figure out better path
  # month plot
  # month_plot(dt_read, name=name, date_col='Date.Read', 
  #            page_col='Number.of.Pages', title_col='Title.Simple',
  #            author_gender_col='gender', lims=c(2010, 2022), save=T)
  # # year plot
  year_plot(dt_read, name=name, fiction_col='Narrative', 
            date_col='Date.Read', page_col='Number.of.Pages', 
            title_col='Title.Simple', author_gender_col='gender', save=T)
  # # summary plot
  summary_plot(dt_read, date_col='Original.Publication.Year', gender_col = 'gender', 
               narrative_col='Narrative', nationality_col='Country.Chosen', 
               authors_database = authors_database, name = name)
}
generate_plots(file_path, name)