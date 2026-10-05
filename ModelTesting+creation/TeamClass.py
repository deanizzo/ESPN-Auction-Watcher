from PlayerClass import Player
class Team:
    def __init__(self, name):
        self.Name = name
        self.Roster = []

        self.Budget = 200

        
        self.TotalRosterSpots = 14

        self.RemainingRosterSpots = 14

        self.MaxBid = self.Budget - self.RemainingRosterSpots +1
        self.RB = 0
        self.WR = 0
        self.TE = 0
        self.QB = 0




    def add_player(self, player:Player):

        self.Roster.append(player)

        self.Budget -= player.AuctionVal
        self.RemainingRosterSpots -= 1

        self.MaxBid = self.Budget - self.RemainingRosterSpots +1
        if (player.Position=="RB"):
            self.RB +=1
        elif (player.Position=="WR"):
            self.WR +=1
        elif (player.Position=="TE"):
            self.TE +=1
        elif (player.Position=="QB"):
            self.QB +=1

    # def __repr__(self):
    #     return (
    #         f"{self.Name}: "
    #         f"${self.Budget} remaining, "
    #         f"{self.RemainingRosterSpots} spots left, "
    #         f"Max Bid = ${self.MaxBid}"
    #     )