require(ggplot2)
require(data.table)
require(forcats)
require(plyr)
require(stringi)
library(rnaturalearth) # for map data
require(RColorBrewer)
require(ggthemes)
setwd('~/Documents/CAL/Real_Life/Repository/Books/')
source('utils.R')
args = commandArgs(trailingOnly=TRUE)
file_path <- args[1]
name <- args[2]
write <- ifelse(length(args) > 2, as.logical(args[3]), F)
start_year <- ifelse(length(args) > 3, as.integer(args[4]), NA)

generate_plots <- function(file_path, name, write=write, start_year.=start_year){
  t1 <- Sys.time()
  dt <- run_all(file_path)
  dt$Source <- name
  dir.create(paste0('Graphs/', name), showWarnings = F)
  authors_database <- read.csv('authors_database.csv')
  # update the authors database based on potential new data from dt
  authors_database <- update_authors_artifact(authors_database, dt, user=name)
  setDT(authors_database)
  print(paste0('Updated authors database - ', Sys.time() - t1))
  dt$gender <- mapvalues(
    dt$Author, 
    authors_database$Author, 
    authors_database$gender_fixed, warn_missing = F)
  dt_read <- dt[Exclusive.Shelf == 'read']
  # read plot
  read_plot(dt_read, name=name, 
            read_col='Read', title_col = 'Title.Simple', plot=T, start_year=start_year
  )
  print(paste0("Read plot created - ", Sys.time() - t1))
  # finish plot
  finish_plot(dt, name = name, plot = T)
  # plot world maps
  world_sf <-
    ne_countries(returnclass = "sf",
                 scale = "large",
                 type = 'map_units')
  world_sf$geounit <-
    mapvalues(
      world_sf$geounit,
      from = c('Gaza', 'West Bank'),
      to = c('Palestine', 'Palestine')
    )
  region_dict <- fread('world_regions_dict.csv')
  region_dict <- region_dict[nationality != '']
  nat_dt <- merge_nationalities(dt, authors_database)
  nationality_bar_plot(dt_read, authors_database, name=name, save=T)
  plot_map_data(nat_dt[Exclusive.Shelf == 'read'], region_dict=region_dict, world_sf=world_sf, user=name)
  print(paste0("Map created - ", Sys.time() - t1))
  # cannot do genre plot with just an individual's data. To figure out better path
  # month plot
  month_plot(dt_read, name=name, date_col='Date.Read', 
             page_col='Number.of.Pages', title_col='Title.Simple',
             author_gender_col='gender', lims=c(2010, 2022), save=T)
  print("Month plot")
  # year plot
  year_plot(dt_read, name=name, fiction_col='Narrative', 
            date_col='Date.Read', page_col='Number.of.Pages', 
            title_col='Title.Simple', author_gender_col='gender', save=T)
  print(paste0('Year Plot created - ', Sys.time() - t1))
  # gender by year
  yearly_gender_graph(dt_read, name=name, date_col='Date.Read', gender_col='gender', 
                       year_start = 2011, save=T)
  # summary plot
  summary_plot(dt_read, date_col='Original.Publication.Year', gender_col = 'gender', 
               narrative_col='Narrative', nationality_col='Country.Chosen', 
               authors_database = authors_database, name = name)
  
  # some top 100 charts
  graph_list(dt_read, 'artifacts/100_books_to_read.csv', '100_Books_to_Read_in_Your_Lifetime', save=T)
  graph_list(dt_read, 'artifacts/100_best_memoirs.csv', '100_Best_Memoirs', save=T)
  graph_list(dt_read, 'artifacts/100_Best_Books_of_the_Decade_2010s.csv', '100_Best_Books_of_the_2010s', save=T)
  if (write == T){
    write.csv(country_dt, file_path, row.names=F)
  }
}
generate_plots(file_path, name, write)