from PlayerClass import Player
from TeamClass import Team


# Stores the completed draft results for each Position + Tier combination.
#
# Example:
# {
#     ("RB", 1): [0.10, 0.08],
#     ("WR", 2): [-0.05, -0.08]
# }
tier_results = {}
# teamsWith6Players = 0
#playerList is a list of type Player
def nominated(player: Player,playerList: list[Player],draftedPlayers: list[Player],teamsWith6Players):
    tierTrend =0
    
    if player.rosterFilled == 6:
        teamsWith6Players += 1

    if player.ProjAuctionVal < 5:   
            player.ModelAuctionProjection = player.ProjAuctionVal
            return teamsWith6Players
    #print(f'nominated:{player.Player}')

    model_projection = player.ProjAuctionVal

    # Tier Adjustment
    tier_key = (
        player.Position,
        player.Tier
    )
    
    #look for players in tier
    if tier_key in tier_results:

        results = tier_results[tier_key]

        increases = []
        decreases = []


        for result in results:

            if result > 0:
                increases.append(result)
            elif result < 0:
                decreases.append(result)
            elif result == 0:
                increases.append(result)
                decreases.append(result)

        diff = len(increases) - len(decreases)
        
        if diff >= 2:
            tierTrend = sum(increases) / len(increases) 

        elif  diff <= -2:
            tierTrend = sum(decreases) / len(decreases)
            


    # Position scarcity adjustment
    # model_projection += position_scarcity_adjustment


    # Team need adjustment
    # model_projection += team_need_adjustment


    # Market inflation adjustment
        # model_projection += market_adjustment
    total_players = 0
    

    x = len(playerList) - len(draftedPlayers)
    # Players still remaining who are eligible for adjustment
    

   
    # print(len(draftedPlayers))
        # Prevent division by zero
    if x > 0 and teamsWith6Players >=6 and player.NomNum <127:
            marketAdjustment = (((player.marketState)-(player.AuctionVal - player.ProjAuctionVal)) / x)

    else:
        marketAdjustment = 0
    # print(marketAdjustment)
    
    # print(marketAdjustment,player.NomNum)
    model_projection = (
        player.ProjAuctionVal +
         (tierTrend * 0.5) + 
         (marketAdjustment*-0.5)

    )
    
        
    player.ModelAuctionProjection = round(model_projection,2)
    return teamsWith6Players


def drafted(player: Player,playerList: list[Player],draftedPlayers: list[Player],teamsWith6Players):

    
    tier_key = (
        player.Position,
        player.Tier
    )


    # Calculate how far the actual auction price was from
    # the original pre-draft projection.
    result = (player.AuctionVal - player.ProjAuctionVal)


    # Create the tier history if necessary.
    if tier_key not in tier_results:

        tier_results[tier_key] = []

    tier_results[tier_key].append(result)

    draftedPlayers.append(player)

    


    
    return teamsWith6Players
    #print(f"Model:{player.ModelAuctionProjection} Proj:{player.ProjAuctionVal} Actual:{player.AuctionVal}")

import pandas as pd

def main(df):
    playerList = []
    for i in range(len(df)):
        # actualTotalp = 0
        # projTotalp = 0
        playerInList = Player(
            player=df.iloc[i]["Player"],
            position=df.iloc[i]["Position"],
            tier=df.iloc[i]["Tier"],
            proj_Auction_Val=df.iloc[i]["projAuction$Adjusted"],
            actual_auction_Val=df.iloc[i]["Auction$"],
            Model_Auction_Projection=0,
            position_rank=df.iloc[i]["PositionRank"],
            overall_rank=df.iloc[i]["OverallRank"],
            team=df.iloc[i]["Team"],
            nomNum=df.iloc[i]["NomOrder"],
            marketState = df.iloc[i]["marketState"],
            rosterFilled = df.iloc[i]["rosterFilled"]
        )
        playerList.append(playerInList)
    
    model_diff = 0
    proj_diff = 0
    
    draftedList = []
    # df2 = []
    teamsWith6Players = 0
    for i in range(len(df)):
        # actualTotalp = 0
        # projTotalp = 0
        nomPlayer = Player(
            player=df.iloc[i]["Player"],
            position=df.iloc[i]["Position"],
            tier=df.iloc[i]["Tier"],
            proj_Auction_Val=df.iloc[i]["projAuction$Adjusted"],
            actual_auction_Val=df.iloc[i]["Auction$"],
            Model_Auction_Projection=0,
            position_rank=df.iloc[i]["PositionRank"],
            overall_rank=df.iloc[i]["OverallRank"],
            team=df.iloc[i]["Team"],
            nomNum=df.iloc[i]["NomOrder"],
            marketState = df.iloc[i]["marketState"],
            rosterFilled = df.iloc[i]["rosterFilled"]
        )
        teamsWith6Players = nominated(nomPlayer,playerList,draftedList,teamsWith6Players)

        model_diff +=abs(nomPlayer.ModelAuctionProjection - nomPlayer.AuctionVal)
        proj_diff +=abs(nomPlayer.ProjAuctionVal - nomPlayer.AuctionVal)
        # if (round(nomPlayer.AuctionVal - nomPlayer.ModelAuctionProjection,2) != round(nomPlayer.AuctionVal - nomPlayer.ProjAuctionVal,2)):
        #     print(round(nomPlayer.AuctionVal - nomPlayer.ModelAuctionProjection,2),round(nomPlayer.AuctionVal - nomPlayer.ProjAuctionVal,2))
        
        # if (nomPlayer.ModelAuctionProjection != nomPlayer.ProjAuctionVal):
        #     # print(round(model_diff,2), nomPlayer.ModelAuctionProjection,nomPlayer.AuctionVal, nomPlayer.ProjAuctionVal)
        #     changediffM += abs(nomPlayer.ModelAuctionProjection - nomPlayer.AuctionVal)
        #     changediffP += abs(nomPlayer.ProjAuctionVal - nomPlayer.AuctionVal)
        
        teamsWith6Players = drafted(nomPlayer,playerList,draftedList,teamsWith6Players)
        #print(marketStateA)
        
        # for j in draftedList:
        #         actualTotalp += j.AuctionVal
        #         projTotalp += j.ProjAuctionVal

        # df2.append({
        #     "NomOrder": nomPlayer.NomNum,
        #     "Actual": actualTotalp,
        #     "Projected": projTotalp
        # })


    # Convert the list into a DataFrame.
    # df2 = pd.DataFrame(df2)
    #print(df2)
    # print(changediffM,changediffP)
    tier_results.clear()

    print(model_diff,proj_diff)
    # return df





if __name__ == "__main__":
    # df1 = None
    # df2 = None
    # df3 = None
    # df4 = None
    for i in [23,24,25,26]:
        # df1 = None
        df = pd.read_csv(f"df{i}.csv")
        df = df.sort_values(by="NomOrder")
        main(df)
        # x = main(df)
        # print(x.iloc[1])
        # if i == 23:
        #     df1 = x
        #     df1.to_csv(f"df{i}.csv")

        # elif i == 24:
        #     df2 = x
        #     df2.to_csv(f"df{i}.csv")

        # elif i == 25:
        #     df3 = x
        #     df3.to_csv(f"df{i}.csv")

        # elif i == 26:
        #     df4 = x
        #     df4.to_csv(f"df{i}.csv")
        

