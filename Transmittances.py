def get_trans():

    # Compute all indexes for different classes individually, and adjust indexes according to canopy thickness (move to separate program)
    VegCoverCategories = [[80, 100], [60, 80], [40, 60], [20, 40], [0, 20]] 
    Transmittances = [0.1, 0.3, 0.5, 0.7, 0.9]                                     
    CanopyTransFactor = 0.5                                                 # Canopy transmission coefficient
    
    return VegCoverCategories,Transmittances,CanopyTransFactor