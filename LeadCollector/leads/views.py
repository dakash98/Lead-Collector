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
        Return a list of all users.
        """
        print("hi i am here")
        pages, total_leads = find_request_count()
        all_leads = fetch_all_lead_objects()
        print(all_leads.count(), total_leads)
        if all_leads.count() == total_leads:
            print("count is same")
            # need to reverse leads
            response_dict = create_response_dict(LeadsModelSerializer(get_reverse_list(all_leads[:20]), many=True).data, pages)
        else:
            print("count is different")
            leads, _ = fetch_paginated_leads(page_no)
            response_dict = create_response_dict(get_reverse_list(leads), pages)
        return Response(response_dict)


def fetch_all_lead_objects():
    return LeadsModel.objects.all()


def create_response_dict(leads, pages):
    return {
            "leads" : leads,
            "count" : pages
        }


def get_reverse_list(all_leads, start_index=0, end_index=20, reverse=False):
    new_lead_list = all_leads[start_index:end_index]
    new_lead_list.reverse() if reverse else None
    return new_lead_list


