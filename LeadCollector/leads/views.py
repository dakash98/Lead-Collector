from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.contrib.auth.models import User
from leads.fetch_lead import fetch_paginated_leads, find_request_count
from leads.models import LeadsModel
from leads.serializers import LeadsModelSerializer

class ListUsers(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    # authentication_classes = [authentication.TokenAuthentication]
    # permission_classes = [permissions.IsAdminUser]

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        usernames = [{"username" : user.username, "email" : user.email} for user in User.objects.all()]
        return Response(usernames)



class FetchLeads(APIView):
    """
    View to list all leads in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    # authentication_classes = [authentication.TokenAuthentication]
    # permission_classes = [permissions.IsAdminUser]

    def get(self, request, page_no):
        """
        Return a list of all leads based on provided page number.
        """
        pages, total_leads = find_request_count()
        if page_no > pages:
            return Response({"Error" : "Provided page does not exist"}, status=404)
        all_leads = fetch_all_lead_objects()
        start_index, end_index= calculate_start_and_end_index(page_no, total_leads)
        leads = fetch_paginated_leads(page_no) if all_leads.count() != total_leads else fetch_all_lead_objects()
        response_dict = create_response_dict(LeadsModelSerializer(get_reverse_list(leads, start_index, end_index), many=True).data, pages)
        return Response(response_dict, status=404)


def fetch_all_lead_objects():
    return LeadsModel.objects.all()


def calculate_start_and_end_index(page, total_leads):
    start_index = (total_leads - 1) if page == 1 else total_leads - 1 - (page-1) * 20 if total_leads - 1 - (page-1) * 20 > 0 else 0
    end_index = total_leads -1 - (page*20) if total_leads-1 - (page*20) > 0 else 0
    print(start_index, end_index)
    return start_index, end_index    


def create_response_dict(leads, pages):
    return {
            "leads" : leads,
            "count" : pages
        }


def get_reverse_list(leads, start_index, end_index):
    return leads[start_index::-1] if (start_index != 0 and end_index == 0) else leads[start_index:end_index:-1]

# from rest_framework.views import APIView
# from rest_framework.response import Response

class UserRegistration(APIView):

    def get(self, request):
        leads_object = LeadsModel.objects.all()
        serialized_data = LeadsModelSerializer(leads_object, many=True).data
        return Response({"leads":serialized_data, "leads_count": len(leads_object)})


    def post(self, request):
        lead_obj = LeadsModel(**request.data)
        lead_obj.save()
        print(request.data)
        return Response(request.data)

