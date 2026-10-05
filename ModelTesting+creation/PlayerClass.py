class Player:
    def __init__(
        self,
        player,
        position,
        tier,
        proj_Auction_Val,
        actual_auction_Val,
        Model_Auction_Projection,
        position_rank,
        overall_rank,
        team,
        nomNum,
        marketState,
        rosterFilled,
        MarketQualified=False
    ):
        self.Player = player
        self.Position = position
        self.Tier = tier
        self.ProjAuctionVal = proj_Auction_Val
        self.AuctionVal = actual_auction_Val
        self.ModelAuctionProjection = Model_Auction_Projection
        self.PositionRank = position_rank
        self.OverallRank = overall_rank
        self.Team = team
        self.NomNum = nomNum
        self.marketState = marketState
        self.rosterFilled = rosterFilled
        self.MarketQualified = MarketQualified

    # def __repr__(self):
    #     return f"{self.Player} ({self.Position})"
    def setAuctionVal(self, x):
        self.AuctionVal = x

    def getAuctionVal(self):
            return self.AuctionVal

    def setModelVal(self,y):
            self.ModelAuctionProjection = y

    def getAuctionVal(self):
            return self.ModelAuctionProjection

    